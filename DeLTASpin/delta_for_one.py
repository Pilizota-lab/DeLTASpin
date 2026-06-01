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

# post-processing of DeLTA output
running_window = 128

# import modules and data
import scipy.io
import numpy as np
from numpy.fft import fft, ifft, fftshift
import os
from datetime import datetime
from scipy.signal import flattop

path = os.path.join(data_folder, "delta_results/Position000000.mat")
try:
    os.mkdir(os.path.join(data_folder, "delta_results/cell info"))
except:
    print("data folder already created")
#load data from .mat file
processed_data = scipy.io.loadmat(path, simplify_cells = True)
cell_info = processed_data["res"]["lineage"]

#find recording parameters
no_of_cells = np.size(cell_info)
no_of_frames = 0 #initialise
for i in range(no_of_cells): #finds max of frames
    try: # account for cells that are only tracked for 1 frame (and results are not in a list)
        if cell_info[i]["frames"][-1] > no_of_frames:
            no_of_frames = cell_info[i]["frames"][-1]
    except:
        pass

no_of_frames = int(no_of_frames)
ts = no_of_frames/fps #length of the whole recording in seconds

"""
go through each cell and:
1. fill in gaps where cell position is missing by interpolating data
2. turn angle into a complex signal
3. do a complex fft on that signal
4. save the data to be compatible with the GUI
"""
spinners = []
biases = []
for cell in range(no_of_cells):
    frames = []
    new_poles = []
    old_poles = []
    try: #account fror cells that are only tracked for 1 frame (i.e., cells that have disappeared from FoV after 1st seq)
        if len(cell_info[cell]["frames"]) >= no_of_frames*0.75: # data mostly complete
            for frame_index in range(len(cell_info[cell]["frames"])-1):
                frames.append(cell_info[cell]["frames"][frame_index])
                new_poles.append(cell_info[cell]["new_pole"][frame_index])
                old_poles.append(cell_info[cell]["old_pole"][frame_index])
                if cell_info[cell]["frames"][frame_index]!=cell_info[cell]["frames"][frame_index+1] - 1:
                    #find how many frames are missing
                    frames_missing = cell_info[cell]["frames"][frame_index+1] - cell_info[cell]["frames"][frame_index] - 1
                    #calculate increments
                    dx_old = (cell_info[cell]["old_pole"][frame_index+1][0] - cell_info[cell]["old_pole"][frame_index][0])/(frames_missing+1)
                    dy_old = (cell_info[cell]["old_pole"][frame_index+1][1] - cell_info[cell]["old_pole"][frame_index][1])/(frames_missing+1)
                    dx_new = (cell_info[cell]["new_pole"][frame_index+1][0] - cell_info[cell]["new_pole"][frame_index][0])/(frames_missing+1)
                    dy_new = (cell_info[cell]["new_pole"][frame_index+1][1] - cell_info[cell]["new_pole"][frame_index][1])/(frames_missing+1)
                    #compute new coordinate values
                    for fr_missing in range(int(frames_missing)):
                        x_old = cell_info[cell]["old_pole"][frame_index][0] + (1+fr_missing)*dx_old
                        y_old = cell_info[cell]["old_pole"][frame_index][1] + (1+fr_missing)*dy_old
                        x_new = cell_info[cell]["new_pole"][frame_index][0] + (1+fr_missing)*dx_new
                        y_new = cell_info[cell]["new_pole"][frame_index][1] + (1+fr_missing)*dy_new
                        frames.append(cell_info[cell]["frames"][frame_index] + fr_missing + 1)
                        new_poles.append([x_new, y_new])
                        old_poles.append([x_old, y_old])
            
            #turn angles into complex signal for current cell
            complex_angles = [] #init
            fft_results = []
            tangents = [] #to save for later
            real_angles = [] #to save for later
            for j in range(0, len(frames)):
                delta_y = old_poles[j][1] - new_poles[j][1]
                delta_x = old_poles[j][0] - new_poles[j][0]
                cell_length = np.sqrt(delta_x**2 + delta_y**2)
                complex_angles.append(complex(delta_x, delta_y))
                real_angles.append(np.arctan(delta_y/delta_x));
                tangents.append(delta_y/delta_x);

            #run FFT on angle-time function - only on the first 1000 fr if more than 1000
            if len(frames)<1000:
                no_pts_fft = len(frames)
            else:
                no_pts_fft = 1000

            fft_results = fft(complex_angles[:no_pts_fft]) #first half the positive values, 2nd half the negative
            fft_shifted = fftshift(fft_results)
            fft_abs = [np.abs(a) for a in fft_shifted]
            frequencies = np.arange(-len(frames[:no_pts_fft])/2, len(frames[:no_pts_fft])/2)*fps/len(frames[:no_pts_fft])

            # plot fourier plots and tangents together - just as test to see if the nan idea works
            # fig, axs = plt.subplots(2, figsize=(15, 8))
            # axs[0].plot(frequencies, fft_abs)
            # axs[0].set_xticks(np.arange(min(frequencies), max(frequencies)+1, 5))
            # axs[0].set_xticks(np.arange(min(frequencies), max(frequencies)+1, 1), minor=True)
            # axs[1].plot([a/fps for a in frames[:1000]], tangents[:1000])
            # axs[0].set_title(f"cell number {cell}")
            # axs[0].set_xlabel("frequency (Hz)")
            # axs[0].set_ylabel("FFT amplitude")
            # axs[1].set_xlabel("time (s)")
            # axs[1].set_ylabel("tangent")
            # plt.tight_layout()
            # plt.savefig(f"C://Users/didic/OneDrive/Desktop/fft optimisation tests/pole problem fixed/fft spectra/cell {cell}.jpg")
            # plt.close()
            # plt.show()

            #select whether spinner or not
            spinner = False

            #first check that there are more than 75% of data points
            #find where frame >= 1000
            datapts_1000 = len([a for a in cell_info[cell]["frames"] if a<=1000])
            if len(cell_info[cell]["frames"])>=len(frames[:1000])*0.75:
                #set the power at frequency 0 to 0
                copy_fft = fft_results
                copy_fft_shifted = [np.abs(a) for a in fftshift(copy_fft)]
                max_power_amplitude = np.max(copy_fft_shifted)
                spinner = False
                max_power_frequency = frequencies[np.argmax(copy_fft_shifted)]
                #threshold
                if (max_power_frequency<-1 or max_power_frequency>1) and max_power_amplitude > 1000:
                    #also make sure that at least 10% of the angles are positive, and 10% negative
                    positive_values = len([a for a in real_angles[:1000] if a>0])
                    negative_values = len([a for a in real_angles[:1000] if a<0])
                    if positive_values>100 and negative_values>100:
                        spinner = True
                        spinners.append(cell)

            timespan = np.arange(0, len(frames)/fps, 1/fps)
            if spinner:
                
                # running_frequencies = np.arange(-running_window/2, running_window/2+1)*fps/running_window
                running_frequencies = np.arange(-running_window/2, running_window/2, 0.5)*fps/running_window # to include extra freq bins for padding
                CW_count = CCW_count = 0
                motor_speeds = []
                for window in range(0, len(frames)-running_window):
                    #apply a window to complex position data
                    # padd with 0s at the end of the row
                    data_window = complex_angles[window:window+running_window]
                    for padd in range(0, 128):
                        data_window.append(0)
                    # hamming_window = flattop(len(complex_angles[window:window+running_window]))
                    fft_window_raw = fft(data_window)
                    fft_window_shift =  [np.abs(a) for a in fftshift(fft_window_raw)]
                    tangent_frequency = running_frequencies[np.argmax(fft_window_shift)]
                    motor_speeds.append(-tangent_frequency)
                    if tangent_frequency>0:
                        CW_count += 1
                    elif tangent_frequency<0:
                        CCW_count += 1
                #compute CW bias
                CW_bias = CW_count/(CW_count+CCW_count)
                # plt.plot(timespan[int(running_window/2):-int(running_window/2)], motor_speeds)
                # plt.savefig(f"C://Users/didic/OneDrive/Desktop/fft optimisation tests/pole problem fixed/motor speeds with padding/speeds_{cell}.jpg")
                # plt.close()
                # print(CW_bias)
                biases.append(CW_bias)

                # save data in dict form
                dict_cell = {
                    "cell_ID": cell,
                    "old_poles": old_poles,
                    "new_poles": new_poles,
                    #general results
                    "timepts": timespan,
                    "angles": real_angles,
                    "tangents": tangents,
                    # for the fft of the first 1000 frames
                    "fft_frequencies": frequencies,
                    "fft_powers": fft_abs,
                    #results for speeds and biases (identified spinners only)
                    "timepts_in_running_window": timespan[int(running_window/2):-int(running_window/2)],
                    "motor_speeds": motor_speeds,
                    "CW_bias": CW_bias,
                    #metadata on analysis parameters
                    "fps": fps,
                    "no_of_frames": len(frames),
                    "path": path
                }
            else: #if not a spinner - save data without spinning data
                dict_cell = {
                    "cell_ID": cell,
                    "old_poles": old_poles,
                    "new_poles": new_poles,
                    #general results
                    "timepts": timespan,
                    "angles": real_angles,
                    "tangents": tangents,
                    "fft_frequencies": frequencies,
                    "fft_powers": fft_abs,
                    #metadata on analysis parameters
                    "fps": fps,
                    "no_of_frames": len(frames),
                    "path": path
                }
            scipy.io.savemat(f"{data_folder}/delta_results/cell info/{cell}.mat", dict_cell)
        else:
            pass # if cell was in the first frame, but disappeared from current timept    
    except:
        pass # if cell was in the first frame, but disappeared from current timept

#save tracked ID of cells which spin (so that you know the name of the .mat files)
f = open(data_folder+"/delta_results/spinners.txt", "w")
f.write(str(spinners))
f.close()

#save CW biases
f = open(data_folder+"/delta_results/cw_biases.txt", "w")
f.write(str(biases))
f.close()




