In this folder, you will find three phase-contrast videos of tethered cells in which CheY** synthesis has been induced at different levels. All videos were recorded at 100 frames per second.

Before analysing the videos, make sure that you extract the files from the archived folders.

Analysing the complete datasets without access to a GPU or high-performance computing cluster may take several hours. Instead, you can use `crop_fov.py` to select a smaller region of the field of view (FoV), such as a single rotating cell or a small group of cells.

## Cropping a dataset

1. Open a terminal, activate the DeLTA environment, and navigate to the folder containing the scripts.

2. Run:

```bash
python crop_fov.py <path_to_dataset>
```

3. A window will open showing a preview of the video, looped continuously.

4. Select the region of the FoV that you would like to analyse and confirm your selection.

5. You will then be asked how many frames you would like to save.

6. The script will create a new folder containing the selected region of the FoV for the requested number of frames.

You can then run DeLTASpin on this smaller dataset.
