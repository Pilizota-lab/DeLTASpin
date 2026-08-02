#!/usr/bin/env python3
"""crop_fov.py -- interactively crop a region of interest from a TIFF video.

Given a folder of phase-contrast TIFF frames (one file per frame) or a single
multi-page TIFF stack, this opens a looping preview of the video, lets you drag
a rectangle over the region you want to keep, then saves that region for the
number of frames you request into a new sibling folder.

Usage:
    python crop_fov.py <path_to_dataset>

Controls in the preview window:
    - drag with the mouse to draw a box; use the handles to fine-tune it
    - "Confirm" button (or press Enter) to accept the selection
    - "Cancel" button (or press Esc) to quit without saving

Optional flags:
    --frames N          save N frames without being prompted
    --fps F             preview playback speed (default 30; recording was 100 fps)
    --preview-frames N  how many frames to load into the loop (default 150)
    --max-display PX    max width/height of the preview window (default 900)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

try:
    import tifffile
except ImportError:
    sys.exit(
        "ERROR: this script needs the 'tifffile' package.\n"
        "Install it inside the DeLTA environment with:\n"
        "    pip install tifffile"
    )

TIFF_EXTS = {".tif", ".tiff"}


# ------------------------------ frame discovery ------------------------------

def natural_key(name: str):
    """Sort key so that frame2 comes before frame10."""
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", name)]


def discover_frames(dataset: Path):
    """Return an ordered list of (path, page) references, one per video frame.

    Two layouts are supported:
      * a folder of single-page TIFFs, one file per frame (the usual case)
      * a single multi-page TIFF stack, where each page is a frame
    """
    if not dataset.exists():
        sys.exit(f"ERROR: path not found: {dataset}")

    if dataset.is_file():
        files = [dataset]
    else:
        files = sorted(
            (p for p in dataset.iterdir()
             if p.is_file() and p.suffix.lower() in TIFF_EXTS),
            key=lambda p: natural_key(p.name),
        )

    if not files:
        sys.exit(f"ERROR: no .tif/.tiff files found in: {dataset}")

    if len(files) == 1:
        with tifffile.TiffFile(files[0]) as tf:
            n_pages = len(tf.pages)
        return [(files[0], i) for i in range(n_pages)]

    return [(f, 0) for f in files]


def read_frame(ref) -> np.ndarray:
    path, page = ref
    return tifffile.imread(path, key=page)


# ------------------------------ preview building -----------------------------

def _to_gray(img: np.ndarray) -> np.ndarray:
    """Collapse a colour image to 2-D; leave grayscale untouched."""
    if img.ndim == 3 and img.shape[-1] in (3, 4):
        return img[..., :3].mean(axis=-1)
    if img.ndim == 3:
        return img[..., 0]
    return img


def build_preview(frames, preview_frames, max_display):
    """Load a down-sampled preview stack for the looping display.

    Returns (preview_stack, step, (vmin, vmax), (full_h, full_w)).
    `step` is the integer down-sampling factor, needed later to map the
    selected ROI back to full-resolution coordinates.
    """
    n = len(frames)
    if n > preview_frames:
        idxs = np.linspace(0, n - 1, preview_frames).astype(int)
    else:
        idxs = np.arange(n)

    first = _to_gray(read_frame(frames[0])).astype(np.float32)
    full_h, full_w = first.shape[:2]
    step = max(1, int(np.ceil(max(full_h, full_w) / float(max_display))))

    # Estimate a display contrast range from a handful of frames.
    sample_ids = idxs[np.linspace(0, len(idxs) - 1,
                                  min(15, len(idxs))).astype(int)]
    sample = np.stack([
        _to_gray(read_frame(frames[i])).astype(np.float32)[::step, ::step]
        for i in sample_ids
    ])
    vmin, vmax = np.percentile(sample, (1, 99))
    if vmax <= vmin:
        vmin, vmax = float(sample.min()), float(sample.min()) + 1.0

    preview = np.stack([
        _to_gray(read_frame(frames[i])).astype(np.float32)[::step, ::step]
        for i in idxs
    ])
    return preview, step, (float(vmin), float(vmax)), (full_h, full_w)


# ------------------------------ ROI selection --------------------------------

def select_roi_gui(preview, vmin, vmax, fps):
    """Show the looping preview and let the user drag a rectangle.

    Returns (xmin, ymin, xmax, ymax) in *preview* pixel coordinates, or None
    if the user cancelled.
    """
    import matplotlib

    # Ensure we have an interactive backend for the pop-up window.
    if matplotlib.get_backend().lower() == "agg":
        for backend in ("TkAgg", "QtAgg", "Qt5Agg", "MacOSX"):
            try:
                matplotlib.use(backend, force=True)
                break
            except Exception:
                continue

    import matplotlib.pyplot as plt
    from matplotlib.widgets import RectangleSelector, Button
    from matplotlib.animation import FuncAnimation

    if matplotlib.get_backend().lower() == "agg":
        sys.exit(
            "ERROR: no interactive matplotlib backend is available, so the\n"
            "preview window cannot be shown. Install one, e.g.:\n"
            "    pip install pyqt5\n"
            "or run this on a machine with a display."
        )

    state = {"extents": None, "confirmed": False}

    fig, ax = plt.subplots(figsize=(8, 8))
    plt.subplots_adjust(bottom=0.14)
    ax.set_title(
        "Drag to select a region; adjust with the handles.\n"
        "Confirm (or press Enter) when happy - Cancel (or Esc) to quit.",
        fontsize=10,
    )
    ax.axis("off")

    im = ax.imshow(preview[0], cmap="gray", vmin=vmin, vmax=vmax)

    n = len(preview)
    counter = {"i": 0}

    def update(_):
        counter["i"] = (counter["i"] + 1) % n
        im.set_array(preview[counter["i"]])
        return (im,)

    anim = None  # keep a reference so it is not garbage-collected
    if n > 1:
        anim = FuncAnimation(
            fig, update, interval=max(1, int(1000 / fps)),
            blit=False, cache_frame_data=False,
        )

    def on_select(eclick, erelease):
        pass  # extents are read from the selector at confirm time

    rs = RectangleSelector(ax, on_select, interactive=True)

    def read_extents():
        ext = getattr(rs, "extents", None)
        if not ext:
            return None
        xmin, xmax, ymin, ymax = ext
        if (xmax - xmin) < 2 or (ymax - ymin) < 2:
            return None
        return (xmin, ymin, xmax, ymax)

    def do_confirm(_evt=None):
        ext = read_extents()
        if ext is None:
            print("Please draw a box before confirming.")
            return
        state["extents"] = ext
        state["confirmed"] = True
        plt.close(fig)

    def do_cancel(_evt=None):
        state["confirmed"] = False
        plt.close(fig)

    def on_key(evt):
        if evt.key in ("enter", "return"):
            do_confirm()
        elif evt.key == "escape":
            do_cancel()

    ax_confirm = fig.add_axes([0.55, 0.03, 0.18, 0.06])
    ax_cancel = fig.add_axes([0.27, 0.03, 0.18, 0.06])
    b_confirm = Button(ax_confirm, "Confirm")
    b_cancel = Button(ax_cancel, "Cancel")
    b_confirm.on_clicked(do_confirm)
    b_cancel.on_clicked(do_cancel)
    fig.canvas.mpl_connect("key_press_event", on_key)

    plt.show()
    _ = anim  # silence "unused" linters; the reference is what matters

    if not state["confirmed"] or state["extents"] is None:
        return None
    return state["extents"]


def roi_to_full(roi_preview, step, full_shape):
    """Map a preview-space ROI back to full-resolution pixel bounds."""
    xmin, ymin, xmax, ymax = roi_preview
    fh, fw = full_shape
    x0 = int(np.floor(xmin * step))
    x1 = int(np.ceil(xmax * step))
    y0 = int(np.floor(ymin * step))
    y1 = int(np.ceil(ymax * step))
    x0 = max(0, min(x0, fw - 1))
    x1 = max(x0 + 1, min(x1, fw))
    y0 = max(0, min(y0, fh - 1))
    y1 = max(y0 + 1, min(y1, fh))
    return x0, y0, x1, y1


# ------------------------------ saving ---------------------------------------

def make_out_dir(dataset: Path) -> Path:
    if dataset.is_file():
        parent, stem = dataset.parent, dataset.stem
    else:
        parent, stem = dataset.parent, dataset.name
    candidate = parent / f"{stem}_crop"
    k = 2
    while candidate.exists():
        candidate = parent / f"{stem}_crop_{k}"
        k += 1
    return candidate


def save_crop(frames, roi_full, n_save, out_dir):
    x0, y0, x1, y1 = roi_full
    out_dir.mkdir(parents=True, exist_ok=True)
    width = max(4, len(str(n_save)))
    for i in range(n_save):
        img = read_frame(frames[i])
        crop = img[y0:y1, x0:x1]  # works for HxW and HxWxC
        tifffile.imwrite(out_dir / f"frame_{i:0{width}d}.tif", crop)
        if (i + 1) % 50 == 0 or (i + 1) == n_save:
            print(f"  saved {i + 1}/{n_save} frames", end="\r", flush=True)
    print()


def ask_n_frames(n_available, preset=None):
    if preset is not None:
        n = max(1, min(preset, n_available))
        if preset > n_available:
            print(f"Only {n_available} frames available; saving {n}.")
        return n
    while True:
        try:
            raw = input(
                f"How many frames would you like to save? "
                f"(1-{n_available}, Enter for all): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)
        if raw == "":
            return n_available
        try:
            v = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if v < 1:
            print("Please enter a positive number.")
            continue
        if v > n_available:
            print(f"Only {n_available} frames are available; saving all of them.")
            return n_available
        return v


# ------------------------------ entry point ----------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(
        description="Interactively crop a region of interest from a TIFF video."
    )
    p.add_argument("dataset", type=Path,
                   help="folder of TIFF frames, or a single multi-page TIFF")
    p.add_argument("--frames", type=int, default=None,
                   help="number of frames to save (skips the prompt)")
    p.add_argument("--fps", type=float, default=30.0,
                   help="preview playback speed (default 30; recorded at 100 fps)")
    p.add_argument("--preview-frames", type=int, default=150,
                   help="how many frames to load into the looping preview")
    p.add_argument("--max-display", type=int, default=900,
                   help="max width/height of the preview window in pixels")
    args = p.parse_args(argv)

    frames = discover_frames(args.dataset)
    n_available = len(frames)
    print(f"Found {n_available} frame(s) in {args.dataset}")

    print("Loading preview...")
    preview, step, (vmin, vmax), full_shape = build_preview(
        frames, args.preview_frames, args.max_display
    )

    roi_preview = select_roi_gui(preview, vmin, vmax, args.fps)
    if roi_preview is None:
        print("No region selected - nothing to do.")
        return 0

    roi_full = roi_to_full(roi_preview, step, full_shape)
    x0, y0, x1, y1 = roi_full
    print(f"Selected region: x {x0}-{x1}, y {y0}-{y1}  "
          f"({x1 - x0}x{y1 - y0} px)")

    n_save = ask_n_frames(n_available, preset=args.frames)

    out_dir = make_out_dir(args.dataset)
    print(f"Saving {n_save} cropped frame(s) to {out_dir}")
    save_crop(frames, roi_full, n_save, out_dir)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
