#this python script allows delta analysis on a single set of images

#find path as command line parameter
import sys
data_folder = sys.argv[1]
extension = sys.argv[2]
population = eval(sys.argv[3])
fps = int(sys.argv[4])

print(extension, type(extension))
print(population, type(population))
print(fps, type(fps))

print(data_folder)
#check GPU is availble
import tensorflow as tf
print(tf.config.list_physical_devices())

#enable memory growth

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except RuntimeError as e:
        print(e)

import os
print(data_folder)
print(len(os.listdir(data_folder)), " files in folder")

import delta
delta.config.load_config(presets="2D")
    

# will have to manually set the extension of the file as the prototypable name needs to contain %04d and 
if extension == "tif":
    prototype = "time_%04d.tif"
elif extension == "bmp":
    prototype = "time_%04d.bmp"
# elif extension == "jpeg": -> this is not gonna work because renaming is hardcoded for 3-letter extension names only (see rename.py)
#     prototype = "time_%04d.jpeg"
elif extension == "jpg":
    prototype = "time_%04d.jpg"
elif extension == "png":
    prototype = "time_%04d.png"
else:
    print("extension not known")

reader = delta.utilities.xpreader(
    data_folder,
    prototype = prototype,
    fileorder='t',
    filenamesindexing=1
)

print("""Initialized experiment reader:
    - %d timepoints"""%(reader.timepoints)
)

# Init Pipeline:
ppln = delta.pipeline.Pipeline(reader)

#print start time here
from datetime import datetime
print("start time is", datetime.now())

# Run it for all frames
# ppln.process(frames=list(range(5)))
ppln.process()
print("end time was", datetime.now())

# the below is an older version of the post-processing code, no longer in use. 
# post-processing of DeLTA output
# running_window = 128

# # import modules and data
# import scipy.io
# import numpy as np
# from numpy.fft import fft, ifft, fftshift
# import os
# from datetime import datetime
# from scipy.signal import flattop

# path = os.path.join(data_folder, "delta_results/Position000000.mat")
# try:
#     os.mkdir(os.path.join(data_folder, "delta_results/cell info"))
# except:
#     print("data folder already created")
# #load data from .mat file
# processed_data = scipy.io.loadmat(path, simplify_cells = True)
# cell_info = processed_data["res"]["lineage"]

# #find recording parameters
# no_of_cells = np.size(cell_info)
# no_of_frames = 0 #initialise
# for i in range(no_of_cells): #finds max of frames
#     try: # account for cells that are only tracked for 1 frame (and results are not in a list)
#         if cell_info[i]["frames"][-1] > no_of_frames:
#             no_of_frames = cell_info[i]["frames"][-1]
#     except:
#         pass

# no_of_frames = int(no_of_frames)
# ts = no_of_frames/fps #length of the whole recording in seconds

# """
# go through each cell and:
# 1. fill in gaps where cell position is missing by interpolating data
# 2. turn angle into a complex signal
# 3. do a complex fft on that signal
# 4. save the data to be compatible with the GUI
# """
# spinners = []
# biases = []
# for cell in range(no_of_cells):
#     frames = []
#     new_poles = []
#     old_poles = []
#     try: #account fror cells that are only tracked for 1 frame (i.e., cells that have disappeared from FoV after 1st seq)
#         if len(cell_info[cell]["frames"]) >= no_of_frames*0.75: # data mostly complete
#             for frame_index in range(len(cell_info[cell]["frames"])-1):
#                 frames.append(cell_info[cell]["frames"][frame_index])
#                 new_poles.append(cell_info[cell]["new_pole"][frame_index])
#                 old_poles.append(cell_info[cell]["old_pole"][frame_index])
#                 if cell_info[cell]["frames"][frame_index]!=cell_info[cell]["frames"][frame_index+1] - 1:
#                     #find how many frames are missing
#                     frames_missing = cell_info[cell]["frames"][frame_index+1] - cell_info[cell]["frames"][frame_index] - 1
#                     #calculate increments
#                     dx_old = (cell_info[cell]["old_pole"][frame_index+1][0] - cell_info[cell]["old_pole"][frame_index][0])/(frames_missing+1)
#                     dy_old = (cell_info[cell]["old_pole"][frame_index+1][1] - cell_info[cell]["old_pole"][frame_index][1])/(frames_missing+1)
#                     dx_new = (cell_info[cell]["new_pole"][frame_index+1][0] - cell_info[cell]["new_pole"][frame_index][0])/(frames_missing+1)
#                     dy_new = (cell_info[cell]["new_pole"][frame_index+1][1] - cell_info[cell]["new_pole"][frame_index][1])/(frames_missing+1)
#                     #compute new coordinate values
#                     for fr_missing in range(int(frames_missing)):
#                         x_old = cell_info[cell]["old_pole"][frame_index][0] + (1+fr_missing)*dx_old
#                         y_old = cell_info[cell]["old_pole"][frame_index][1] + (1+fr_missing)*dy_old
#                         x_new = cell_info[cell]["new_pole"][frame_index][0] + (1+fr_missing)*dx_new
#                         y_new = cell_info[cell]["new_pole"][frame_index][1] + (1+fr_missing)*dy_new
#                         frames.append(cell_info[cell]["frames"][frame_index] + fr_missing + 1)
#                         new_poles.append([x_new, y_new])
#                         old_poles.append([x_old, y_old])
            
#             #turn angles into complex signal for current cell
#             complex_angles = [] #init
#             fft_results = []
#             tangents = [] #to save for later
#             real_angles = [] #to save for later
#             for j in range(0, len(frames)):
#                 delta_y = old_poles[j][1] - new_poles[j][1]
#                 delta_x = old_poles[j][0] - new_poles[j][0]
#                 cell_length = np.sqrt(delta_x**2 + delta_y**2)
#                 complex_angles.append(complex(delta_x, delta_y))
#                 real_angles.append(np.arctan(delta_y/delta_x));
#                 tangents.append(delta_y/delta_x);

#             #run FFT on angle-time function - only on the first 1000 fr if more than 1000
#             if len(frames)<1000:
#                 no_pts_fft = len(frames)
#             else:
#                 no_pts_fft = 1000

#             fft_results = fft(complex_angles[:no_pts_fft]) #first half the positive values, 2nd half the negative
#             fft_shifted = fftshift(fft_results)
#             fft_abs = [np.abs(a) for a in fft_shifted]
#             frequencies = np.arange(-len(frames[:no_pts_fft])/2, len(frames[:no_pts_fft])/2)*fps/len(frames[:no_pts_fft])

#             # plot fourier plots and tangents together - just as test to see if the nan idea works
#             # fig, axs = plt.subplots(2, figsize=(15, 8))
#             # axs[0].plot(frequencies, fft_abs)
#             # axs[0].set_xticks(np.arange(min(frequencies), max(frequencies)+1, 5))
#             # axs[0].set_xticks(np.arange(min(frequencies), max(frequencies)+1, 1), minor=True)
#             # axs[1].plot([a/fps for a in frames[:1000]], tangents[:1000])
#             # axs[0].set_title(f"cell number {cell}")
#             # axs[0].set_xlabel("frequency (Hz)")
#             # axs[0].set_ylabel("FFT amplitude")
#             # axs[1].set_xlabel("time (s)")
#             # axs[1].set_ylabel("tangent")
#             # plt.tight_layout()
#             # plt.savefig(f"C://Users/didic/OneDrive/Desktop/fft optimisation tests/pole problem fixed/fft spectra/cell {cell}.jpg")
#             # plt.close()
#             # plt.show()

#             #select whether spinner or not
#             spinner = False

#             #first check that there are more than 75% of data points
#             #find where frame >= 1000
#             datapts_1000 = len([a for a in cell_info[cell]["frames"] if a<=1000])
#             if len(cell_info[cell]["frames"])>=len(frames[:1000])*0.75:
#                 #set the power at frequency 0 to 0
#                 copy_fft = fft_results
#                 copy_fft_shifted = [np.abs(a) for a in fftshift(copy_fft)]
#                 max_power_amplitude = np.max(copy_fft_shifted)
#                 spinner = False
#                 max_power_frequency = frequencies[np.argmax(copy_fft_shifted)]
#                 #threshold
#                 if (max_power_frequency<-1 or max_power_frequency>1) and max_power_amplitude > 1000:
#                     #also make sure that at least 10% of the angles are positive, and 10% negative
#                     positive_values = len([a for a in real_angles[:1000] if a>0])
#                     negative_values = len([a for a in real_angles[:1000] if a<0])
#                     if positive_values>100 and negative_values>100:
#                         spinner = True
#                         spinners.append(cell)

#             timespan = np.arange(0, len(frames)/fps, 1/fps)
#             if spinner:
                
#                 # running_frequencies = np.arange(-running_window/2, running_window/2+1)*fps/running_window
#                 running_frequencies = np.arange(-running_window/2, running_window/2, 0.5)*fps/running_window # to include extra freq bins for padding
#                 CW_count = CCW_count = 0
#                 motor_speeds = []
#                 for window in range(0, len(frames)-running_window):
#                     #apply a window to complex position data
#                     # padd with 0s at the end of the row
#                     data_window = complex_angles[window:window+running_window]
#                     for padd in range(0, 128):
#                         data_window.append(0)
#                     # hamming_window = flattop(len(complex_angles[window:window+running_window]))
#                     fft_window_raw = fft(data_window)
#                     fft_window_shift =  [np.abs(a) for a in fftshift(fft_window_raw)]
#                     tangent_frequency = running_frequencies[np.argmax(fft_window_shift)]
#                     motor_speeds.append(-tangent_frequency)
#                     if tangent_frequency>0:
#                         CW_count += 1
#                     elif tangent_frequency<0:
#                         CCW_count += 1
#                 #compute CW bias
#                 CW_bias = CW_count/(CW_count+CCW_count)
#                 # plt.plot(timespan[int(running_window/2):-int(running_window/2)], motor_speeds)
#                 # plt.savefig(f"C://Users/didic/OneDrive/Desktop/fft optimisation tests/pole problem fixed/motor speeds with padding/speeds_{cell}.jpg")
#                 # plt.close()
#                 # print(CW_bias)
#                 biases.append(CW_bias)

#                 # save data in dict form
#                 dict_cell = {
#                     "cell_ID": cell,
#                     "old_poles": old_poles,
#                     "new_poles": new_poles,
#                     #general results
#                     "timepts": timespan,
#                     "angles": real_angles,
#                     "tangents": tangents,
#                     # for the fft of the first 1000 frames
#                     "fft_frequencies": frequencies,
#                     "fft_powers": fft_abs,
#                     #results for speeds and biases (identified spinners only)
#                     "timepts_in_running_window": timespan[int(running_window/2):-int(running_window/2)],
#                     "motor_speeds": motor_speeds,
#                     "CW_bias": CW_bias,
#                     #metadata on analysis parameters
#                     "fps": fps,
#                     "no_of_frames": len(frames),
#                     "path": path
#                 }
#             else: #if not a spinner - save data without spinning data
#                 dict_cell = {
#                     "cell_ID": cell,
#                     "old_poles": old_poles,
#                     "new_poles": new_poles,
#                     #general results
#                     "timepts": timespan,
#                     "angles": real_angles,
#                     "tangents": tangents,
#                     "fft_frequencies": frequencies,
#                     "fft_powers": fft_abs,
#                     #metadata on analysis parameters
#                     "fps": fps,
#                     "no_of_frames": len(frames),
#                     "path": path
#                 }
#             scipy.io.savemat(f"{data_folder}/delta_results/cell info/{cell}.mat", dict_cell)
#         else:
#             pass # if cell was in the first frame, but disappeared from current timept    
#     except:
#         pass # if cell was in the first frame, but disappeared from current timept

# #save tracked ID of cells which spin (so that you know the name of the .mat files)
# f = open(data_folder+"/delta_results/spinners.txt", "w")
# f.write(str(spinners))
# f.close()

# #save CW biases
# f = open(data_folder+"/delta_results/cw_biases.txt", "w")
# f.write(str(biases))
# f.close()

# below are all the functions required to analyse delta output and get motor traces and CW biases
import scipy.io
import numpy as np
from numpy.fft import fft, fftshift
import os
# from scipy.signal import flattop
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. filters for identifying tracking errors and correct them where possible
# ---------------------------------------------------------------------------

def mad(x):
    # using MAD (median absolute deviation) - more robust compared to using stdev
    x = np.asarray(x, dtype=float)
    med = np.nanmedian(x)
    mad = np.nanmedian(np.abs(x - med))
    return mad


def detect_outliers_centre_change(new_pole, old_pole, n_mads=4.5, min_threshold_norm=0.2):
    """
    Detect one-frame identity-switch-like events using frame-to-frame
    centre displacement.

    A frame t is marked as bad if:
        centre jump from t-1 to t is unusually large
        AND
        centre jump from t to t+1 is unusually large

    The threshold is:
        median(centre_step) + n_mads * mad
    """

    new_pole = np.asarray(new_pole, dtype=float)
    old_pole = np.asarray(old_pole, dtype=float)

    # get centre
    centre = 0.5 * (new_pole + old_pole) # 2D array (both x and y coords over time)
    # get cell centre and length
    dx = new_pole[:, 0] - old_pole[:, 0]
    dy = new_pole[:, 1] - old_pole[:, 1]
    cell_length = np.sqrt(dx**2 + dy**2)
    median_cell_length = np.nanmedian(cell_length)

    centre_dx = np.diff(centre[:, 0])
    centre_dy = np.diff(centre[:, 1])
    centre_change_px = np.sqrt(centre_dx**2 + centre_dy**2) # distance travelled by centre from frame to frame (not accounting for missing frames -> that's why tneed to check that it's a spike)
    # normalise centre by cell length (consistency across cell lengths and magnifications/optical systems)
    centre_change = centre_change_px / median_cell_length

    med = np.nanmedian(centre_change)
    MAD = mad(centre_change)

    threshold = med + n_mads * MAD
    threshold = max(threshold, min_threshold_norm) # for cells that are stuck and will result in very small (and therefore sensitive) MADs

    # check whether both changes are big changes (spike?)
    # create masks for points that have not been 
    outliers_mask = np.zeros(len(new_pole), dtype=bool) # initialise mask

    for frame_idx in range(1, len(centre_change)):

        jump_into_frame = centre_change[frame_idx - 1] #previous
        jump_out_of_frame = centre_change[frame_idx]

        jump_into_is_large = jump_into_frame > threshold
        jump_out_is_large = jump_out_of_frame > threshold

        if jump_into_is_large and jump_out_is_large:
            outliers_mask[frame_idx] = True

    return outliers_mask


def detect_outliers_coordinate_change(new_pole, old_pole, n_mads=4.5, min_threshold_norm=0.2):
    """
    similar to the previous filter, this is detecting one-frame spikes in any of the 4 pole coordinates. 
    for extra robustness (there are cases in which the previous filter is not enough)
    """

    new_pole = np.asarray(new_pole, dtype=float)
    old_pole = np.asarray(old_pole, dtype=float)
    dx = new_pole[:, 0] - old_pole[:, 0]
    dy = new_pole[:, 1] - old_pole[:, 1]
    cell_length = np.sqrt(dx**2 + dy**2)
    median_cell_length = np.nanmedian(cell_length)

    traces = {
        "new_x": new_pole[:, 0],
        "new_y": new_pole[:, 1],
        "old_x": old_pole[:, 0],
        "old_y": old_pole[:, 1],
    }


    overall_mask = np.zeros(len(cell_length), dtype=bool)
    for coord, data in traces.items():
        data = np.asarray(data, dtype=float)
        coord_change_px = np.abs(np.diff(data))
        coord_change = coord_change_px / median_cell_length

        # calculate threshold
        med = np.nanmedian(coord_change)
        MAD = mad(coord_change)
        threshold = med + n_mads * MAD
        threshold = max(threshold, min_threshold_norm)

        outliers_mask = np.zeros(len(cell_length), dtype=bool)
        for frame_idx in range(1, len(coord_change)):
            jump_into_frame = coord_change[frame_idx - 1]
            jump_out_of_frame = coord_change[frame_idx]

            if jump_into_frame > threshold and jump_out_of_frame > threshold:
                outliers_mask[frame_idx] = True

        # pass the True vals found in current coordinate to the overall mask
        overall_mask = overall_mask | outliers_mask #OR

    return overall_mask



def mark_pole_switches(new_pole, old_pole, frames):
    """
    TO BE USED AFTER FILTERING OUTLIERS - make sure indices are reset after filtering!!
    checks again the euclidian distance from the previous (valid this time) point - if wrong, remember where this is
    I also would have liked to account for the issues with the "angle sweeped more than 90 degrees between 2 valid frames" issue, but I can't find a way to do this geometrically (nor have i found a situation in which this happens)
    """
    new_pole = np.asarray(new_pole, dtype=float)
    old_pole = np.asarray(old_pole, dtype=float)
    frames = np.asarray(frames, dtype=float)

    switch_mask = np.zeros(len(new_pole), dtype=bool) # returns frames at which switches occured

    for tp in range(1, len(new_pole)): # these are just the valid time points - remember to reset indiced after filtering!!!
        # check euclidian distance between consecutive (valid) points (after outliers have been filtered)
        new_pole_1 = new_pole[tp] # current frame
        old_pole_1 = old_pole[tp] 
        new_pole_0 = new_pole[tp-1] # previous (valid) frame
        old_pole_0 = old_pole[tp-1]
        distance_assigned = np.sqrt((new_pole_1[0] - new_pole_0[0])**2 + (new_pole_1[1] - new_pole_0[1])**2) + np.sqrt((old_pole_1[0] - old_pole_0[0])**2 + (old_pole_1[1] - old_pole_0[1])**2)
        distance_inverted = np.sqrt((old_pole_1[0] - new_pole_0[0])**2 + (old_pole_1[1] - new_pole_0[1])**2) + np.sqrt((new_pole_1[0] - old_pole_0[0])**2 + (new_pole_1[1] - old_pole_0[1])**2)

        if distance_inverted < distance_assigned:
            switch_mask[tp] = True # this will contain all frames in which the poles had to be swapped, and not the actual switching events
    
    return switch_mask


def get_aliasing_mask(new_pole, old_pole, frames, fps, most_powerful_freq, max_angle_allowed = 90):
    """
    angle to be given in degrees
    somewhat misleading name because it also checks for potential pole switching due to angle being too large
    but this will take the main peak and check 
    """
    max_gap_allowed =fps*max_angle_allowed/(most_powerful_freq*360) # in number of frames
    max_gap_allowed = max(1, max_gap_allowed)
    alias_mask = np.zeros(len(new_pole), dtype=bool) # returns frames at which switches occured
    for fr in range(1, len(frames)):
        if frames[fr] - frames[fr-1] > max_gap_allowed:
            alias_mask[fr] = True 
    return alias_mask


# --------------------
# 2. spinner classification
# --------------------


def classify_spinners(path, cell_id, new_poles, old_poles, frames, fps, amplitude_threshold):
    """
    takes filtered data and interpolates for missing frames (normal FFT assumes evently spaced sampling)
    does FFT
    returns a list cell IDs for spinners + a dictionary with amplitudes and freqs for spinners only (for plotting)
    also saves to disk "FFT results" for each cell (only if coverage is >75%., mat files)
    """
    # find missing time intervals and interpolate for fft
    interpolated_frames = []
    interpolated_new_poles = []
    interpolated_old_poles = []

    for frame_index in range(len(frames)-1):
        interpolated_frames.append(frames[frame_index])
        interpolated_new_poles.append(new_poles[frame_index])
        interpolated_old_poles.append(old_poles[frame_index])
        if frames[frame_index]!=frames[frame_index+1] - 1: # if not consecutive
            #find how many frames are missing
            frames_missing = frames[frame_index+1] - frames[frame_index] - 1
            #calculate increments
            dx_old = (old_poles[frame_index+1][0] - old_poles[frame_index][0])/(frames_missing+1)
            dy_old = (old_poles[frame_index+1][1] - old_poles[frame_index][1])/(frames_missing+1)
            dx_new = (new_poles[frame_index+1][0] - new_poles[frame_index][0])/(frames_missing+1)
            dy_new = (new_poles[frame_index+1][1] - new_poles[frame_index][1])/(frames_missing+1)
            #compute new coordinate values
            for fr_missing in range(int(frames_missing)):
                x_old = old_poles[frame_index][0] + (1+fr_missing)*dx_old
                y_old = old_poles[frame_index][1] + (1+fr_missing)*dy_old
                x_new = new_poles[frame_index][0] + (1+fr_missing)*dx_new
                y_new = new_poles[frame_index][1] + (1+fr_missing)*dy_new
                interpolated_frames.append(frames[frame_index] + fr_missing + 1)
                interpolated_new_poles.append([x_new, y_new])
                interpolated_old_poles.append([x_old, y_old])
    interpolated_frames.append(frames[-1])
    interpolated_new_poles.append(new_poles[-1])
    interpolated_old_poles.append(old_poles[-1])

    #turn angles into complex vector for current cell
    complex_signal = [] #init
    fft_results = []
    for j in range(0, len(interpolated_frames)):
        delta_y = interpolated_old_poles[j][1] - interpolated_new_poles[j][1]
        delta_x = interpolated_old_poles[j][0] - interpolated_new_poles[j][0]
        cell_length = np.sqrt(delta_x**2 + delta_y**2)
        complex_signal.append(complex(delta_x, delta_y) / cell_length) # normalise by cell length
    fft_results = fft(complex_signal) #first half the positive values, 2nd half the negative
    fft_shifted = fftshift(fft_results)
    fft_abs_norm = [np.abs(a)/len(complex_signal) for a in fft_shifted]
    freq_bins = np.fft.fftshift(np.fft.fftfreq(len(interpolated_frames), d=1/fps))

    #select whether spinner or not
    max_idx = np.argmax(fft_abs_norm)
    max_FFT_amplitude = fft_abs_norm[max_idx]
    max_power_frequency = freq_bins[max_idx]
    spinner = False
    # check if above thresholds
    if np.abs(max_power_frequency)>1 and max_FFT_amplitude > amplitude_threshold:
        # the comments below are lefover from some algorithm i was trying before, but not needed anymore. left just in case
        # #also make sure that at least 10% of the angles are positive, and 10% negative
        # positive_values = len([a for a in real_angles[:1000] if a>0])
        # negative_values = len([a for a in real_angles[:1000] if a<0])
        # if positive_values>100 and negative_values>100:
        #     spinner = True
        #     spinners.append(cell)
        spinner = True

    #save fft results
    dict_cell_to_save = {
        "cell_ID": cell_id,
        "frequency_bins": freq_bins,
        "fft_amplitudes": fft_abs_norm,
        "fps": fps,
    }
    os.makedirs(f"{path}/delta_results/new_analysis/FFT results", exist_ok=True)
    scipy.io.savemat(f"{path}/delta_results/new_analysis/FFT results/{cell_id}.mat", dict_cell_to_save)

    return spinner, freq_bins, fft_abs_norm




# -----------------
# 3. function to work out "instantaneous" motor speed (slope fitting with a sliding window)
# ----------------

def get_motor_frequency(new_poles, old_poles, frames, window=10, fps=95, switch_mask=None):
    """Return (times, frequency_hz) for one cell using a rolling linear fit."""

    new_pole = np.asarray(new_poles, dtype=float)
    old_pole = np.asarray(old_poles, dtype=float)
    frames   = np.asarray(frames, dtype=float)

    if switch_mask is None:
        switch_mask = np.zeros(len(frames), dtype=bool)
    else:
        switch_mask = np.asarray(switch_mask, dtype=bool)

    dx = new_pole[:, 0] - old_pole[:, 0]
    dy = new_pole[:, 1] - old_pole[:, 1]
    angle_deg = np.degrees(np.unwrap(np.arctan2(dy, dx)))

    times = frames / fps   # time points (in seconds)
    speed_times, freq_hz = [], []
    for start in range(len(times) - window + 1):
        end = start + window

        if np.any(switch_mask[start + 1:end]):
            continue

        slope = np.polyfit(times[start:end], angle_deg[start:end], 1)[0]  #deg/s
        speed_times.append(times[start + window // 2])
        freq_hz.append(slope / 360)  #Hz

    return np.array(speed_times), np.array(freq_hz)


# -----------------------
# 4. plot results for spinner
# -------------------------

def plotter_function(
        cell_id,
        new_poles,
        old_poles,
        frames,
        fps,
        outliers_mask,
        switch_mask,
        alias_mask,
        fft_bins,
        fft_amplitudes,
        motor_times,
        motor_speeds,
        window,
        save_to,
):
    
    to_keep = ~outliers_mask
    filtered_new_poles = new_poles[to_keep]
    filtered_old_poles = old_poles[to_keep]
    filtered_frames = frames[to_keep]


    t_raw = frames / fps
    t_filtered = filtered_frames / fps

    switch_times = filtered_frames[switch_mask] / fps
    alias_times = filtered_frames[alias_mask] / fps

    fig, ax = plt.subplots(4, figsize=(13, 13))

    def centre_y_axis(ax_, y_values, padding=1.05):
        y_values = np.asarray(y_values, dtype=float)
        if np.all(np.isnan(y_values)):
            max_abs = 1
        else:
            max_abs = np.nanmax(np.abs(y_values))
        if max_abs == 0 or np.isnan(max_abs):
            max_abs = 1
        ax_.set_ylim(-padding * max_abs, padding * max_abs)
        ax_.axhline(0, color="0.25", lw=1.2, ls="--", dashes=(7, 4), zorder=0)

    def add_event_lines(ax_):
        first_switch = True
        first_alias = True
        for st in switch_times:
            ax_.axvline(st, color="cyan", lw=1, ls=":", zorder=0, label="pole switch" if first_switch else None)
            first_switch = False
        for at in alias_times:
            ax_.axvline(at, color="magenta", lw=1, ls=":", zorder=0, label="large gap" if first_alias else None)
            first_alias = False

    fig.suptitle(f"cell {cell_id}")

    COORD_COLOURS = {
        "new x": "tab:blue",
        "new y": "tab:cyan",
        "old x": "tab:orange",
        "old y": "tab:red",
    }

    coords = {
        "new x": new_poles[:, 0],
        "new y": new_poles[:, 1],
        "old x": old_poles[:, 0],
        "old y": old_poles[:, 1],
    }

    # 1. raw coordinate displacements, with outliers marked
    all_coord_disps = []
    first_outlier = True

    for label, c in coords.items():
        disp = c - np.nanmedian(c)
        all_coord_disps.append(disp)
        ax[0].plot(t_raw, disp, label=label, color=COORD_COLOURS[label])

        idx = np.where(outliers_mask)[0]
        if len(idx) > 0:
            ax[0].scatter(t_raw[idx], disp[idx], marker="x", color="black", s=55, linewidths=1.5, zorder=5, label="outlier" if first_outlier else None)
            first_outlier = False

    add_event_lines(ax[0])
    centre_y_axis(ax[0], np.concatenate(all_coord_disps))
    ax[0].set(title="coordinate displacements", ylabel="coordinate displacement (px)")
    ax[0].legend(fontsize=8, ncol=3)

    # 2. wrapped angle after outlier removal
    dx = filtered_new_poles[:, 0] - filtered_old_poles[:, 0]
    dy = filtered_new_poles[:, 1] - filtered_old_poles[:, 1]
    angle_after_filtering = np.degrees(np.arctan2(dy, dx))

    ax[1].plot(t_filtered, angle_after_filtering, color="black", lw=1, zorder=1)
    ax[1].scatter(t_filtered, angle_after_filtering, s=5, color="black", zorder=2, label="angle")
    add_event_lines(ax[1])
    centre_y_axis(ax[1], angle_after_filtering)
    ax[1].set(title="wrapped angle after outlier removal", ylabel="angle (deg)")
    ax[1].legend(fontsize=8)

    # 3. motor speed before and after filtering/skips
    t_before, f_before = get_motor_frequency(new_poles, old_poles, frames, window=window, fps=fps)
    t_after, f_after = motor_times, motor_speeds

    ax[2].scatter(t_before, [-a for a in f_before], s=7, color="gray", label="before filtering/skips")
    ax[2].scatter(t_after, [-a for a in f_after], s=7, color="black", label="after filtering/skips")
    add_event_lines(ax[2])

    if len(f_before) or len(f_after):
        centre_y_axis(ax[2], np.concatenate([np.asarray(f_before, dtype=float), np.asarray(f_after, dtype=float)]))

    ax[2].set(title="motor speed", ylabel="motor frequency (Hz)")
    ax[2].legend(fontsize=8)

    # 4. FFT spectrum
    fft_bins = np.asarray(fft_bins, dtype=float)
    fft_amplitudes = np.asarray(fft_amplitudes, dtype=float)

    ax[3].plot(fft_bins, fft_amplitudes, color="black", lw=1)
    ax[3].scatter(fft_bins, fft_amplitudes, color="black", s=6)
    ax[3].set(title="FFT spectrum", xlabel="frequency (Hz)", ylabel="FFT amplitude")

    if len(fft_bins) > 0:
        x_min = np.floor(np.nanmin(fft_bins) / 5) * 5
        x_max = np.ceil(np.nanmax(fft_bins) / 5) * 5
        ax[3].set_xticks(np.arange(x_min, x_max + 5, 5))

    if len(fft_amplitudes) > 0:
        y_max = np.nanmax(fft_amplitudes)
        if np.isfinite(y_max):
            y_top = np.ceil(y_max / 0.1) * 0.1
            if y_top == 0:
                y_top = 0.1
            ax[3].set_yticks(np.arange(0, y_top + 0.1, 0.1))
            ax[3].set_ylim(0, y_top * 1.05)

    ax[3].grid(True, which="major", axis="both", alpha=0.35)
    ax[3].axvline(1, color="red", linestyle="--", lw=1, label="1 Hz threshold")
    ax[3].axvline(-1, color="red", linestyle="--", lw=1, label="-1 Hz threshold")
    ax[3].axhline(0.2, color="red", linestyle="--", lw=1, label="amplitude threshold")
    ax[3].legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(save_to, dpi=150)
    plt.close(fig)




# --------------------------
# 5. pipeline runner
# ------------------------

def run_postprocessing(
        path, 
        fps,
        n_mads = 4.5, 
        min_threshold_norm = 0.2,
        amplitude_threshold = 0.2,
        max_angle_allowed = 90,
        window=10,
        filters = True
):
    
    """
    this function runs the whole pipeline;
    just call from main
    path = path to dataset itself (not to "delta_results")
    """
    processed_data = scipy.io.loadmat(
        os.path.join(path, "delta_results", "Position000000.mat"),
        simplify_cells=True
    )
    cell_info = processed_data["res"]["lineage"]

    # will iterate over each cell
    no_of_cells = np.size(cell_info)
    no_of_frames = 0 #initialise


    for i in range(no_of_cells): #finds max of frames
        try: # account for cells that are only tracked for 1 frame (and results are not in a list)
            if cell_info[i]["frames"][-1] > no_of_frames:
                no_of_frames = cell_info[i]["frames"][-1]
        except:
            pass

    no_of_frames = int(no_of_frames)

    spinners = []
    cwbs = []
    final_coverages = []
    for cell in range(no_of_cells):
        # first check coverage
        if not isinstance(cell_info[cell]["frames"], np.ndarray):
            continue
        if len(cell_info[cell]["frames"])/no_of_frames <= 0.75:
            continue

        raw_frames = np.asarray(cell_info[cell]["frames"])
        raw_old_poles = np.asarray(cell_info[cell]["old_pole"])
        raw_new_poles = np.asarray(cell_info[cell]["new_pole"])

        if filters:
            mask_A = detect_outliers_centre_change(raw_new_poles, raw_old_poles, n_mads=n_mads, min_threshold_norm=min_threshold_norm)
            mask_B = detect_outliers_coordinate_change(raw_new_poles, raw_old_poles, n_mads=n_mads, min_threshold_norm=min_threshold_norm)
            to_remove = mask_A | mask_B 
            to_keep = ~to_remove
            filtered_frames = raw_frames[to_keep]
            filtered_old_poles = raw_old_poles[to_keep]
            filtered_new_poles = raw_new_poles[to_keep]
        else:
            filtered_frames = raw_frames
            filtered_old_poles = raw_old_poles
            filtered_new_poles = raw_new_poles
            to_remove = np.zeros(len(raw_frames), dtype=bool)
            to_keep = ~to_remove

        spinner, freq_bins, fft_amplitudes = classify_spinners(path, cell, filtered_new_poles, filtered_old_poles, filtered_frames, fps=fps, amplitude_threshold=amplitude_threshold)
        if spinner:
            # run pole switch and aliasing check
            switch_mask = mark_pole_switches(filtered_new_poles, filtered_old_poles, filtered_frames)
            alias_mask = get_aliasing_mask(filtered_new_poles, filtered_old_poles, filtered_frames, 
                                           fps = fps,
                                           most_powerful_freq = abs(freq_bins[np.argmax(fft_amplitudes)]), # I need positive frequency
                                           max_angle_allowed=max_angle_allowed)
            break_mask = switch_mask | alias_mask
            motor_times, motor_speeds = get_motor_frequency(filtered_new_poles, 
                                                            filtered_old_poles,
                                                            filtered_frames,
                                                            window = window,
                                                            fps = fps, 
                                                            switch_mask=break_mask
                                                            )
            # calculate clockwise bias
            no_CW = len([a for a in motor_speeds if a > 0.4])
            no_CCW = len([a for a in motor_speeds if a <-0.4])
            if no_CW+no_CCW == 0:
                continue
            cwb = no_CW/(no_CW+no_CCW)

            # calculate "spinner scores"
            total_valid_recording = len(motor_speeds)/fps # in seconds
            percentage_coverage_left = len(motor_speeds)/len(raw_new_poles) # out of what was put in (after filtering and skipping)
            if total_valid_recording > 3: # if less than 3s, no point in keeping   
                # save outputs
                spinner_dictionary = {
                    "cell_ID": cell,
                    "times": motor_times,
                    "motor_speeds": [-a for a in motor_speeds], # invert because i'm looking from the "wrong" side
                    "cw_bias": cwb,
                    "valid_recording": total_valid_recording,
                    "coverage_left": percentage_coverage_left
                }
                spinners.append(cell)
                cwbs.append(cwb)
                final_coverages.append(total_valid_recording)
                os.makedirs(f"{path}/delta_results/new_analysis/spinner speeds", exist_ok=True)
                scipy.io.savemat(f"{path}/delta_results/new_analysis/spinner speeds/{cell}.mat", spinner_dictionary)
                # remember to also make plot!!!! 
                os.makedirs(f"{path}/delta_results/new_analysis/spinner plots", exist_ok=True)
                plotter_function(
                    cell,
                    raw_new_poles, 
                    raw_old_poles, 
                    raw_frames, 
                    fps, 
                    to_remove, 
                    switch_mask, 
                    alias_mask, 
                    freq_bins, 
                    fft_amplitudes, 
                    motor_times, 
                    motor_speeds,
                    window,
                    save_to=f"{path}/delta_results/new_analysis/spinner plots/{cell}.jpg")


    #save tracked ID of spinners (so that you know the name of the .mat files)
    f = open(path + "/delta_results/new_analysis/spinners.txt", "w")
    f.write(str(spinners))
    f.close()
    f = open(path + "/delta_results/new_analysis/cw_biases.txt", "w")
    f.write(str(cwbs))
    f.close()
    f = open(path + "/delta_results/new_analysis/final_coverage_s.txt", "w")
    f.write(str(final_coverages))
    f.close()

# run postprocessing pipeline
run_postprocessing(os.path.join(data_folder, "delta_results"), fps=fps)
