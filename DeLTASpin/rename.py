# this script will:
# 1. rename the images in each folder in the time_04d format
# 2. if required, move the first frame from first time point to all the other time points

import sys
print(sys.argv[1])
print(sys.argv[2])
print(sys.argv[3])
print(sys.argv[4])

alldata = sys.argv[1] # path to folder with all data from current date
extension = sys.argv[2]
population = eval(sys.argv[3])
fps = int(sys.argv[4])

print(extension, type(extension))
print(population, type(population))
print(fps, type(fps))

import os

def rename(img_directory, ext):
    '''
    this function renames all image sequences collected from microscope
    only run it once, otherwise it will through an error
    '''
    #choose image sequence 
    import os
    import re
    #check if names have already been changed
    if re.match("time_(\d{4}).%s"%ext,os.listdir(img_directory)[0])!=True:
        #rename all images in the image sequence in a prototypable way
        for img in os.listdir(img_directory):
            if re.match(r"(.*)(\D)(\d){1}.%s"%ext, img):
                os.rename(f"{img_directory}/{img}", f"{img_directory}/time_000{img[-5:]}")
                print(img)
            else: #fewer operations if it goes in this order
                if re.match(r"(.*)(\D)(\d){2}.%s"%ext, img):
                    os.rename(f"{img_directory}/{img}", f"{img_directory}/time_00{img[-6:]}")
                else:
                    if re.match(r"(.*)(\D)(\d){3}.%s"%ext, img):
                        os.rename(f"{img_directory}/{img}", f"{img_directory}/time_0{img[-7:]}")
                    else:
                        if re.match(r"(.*)(\D)(\d){4}.%s"%ext, img):
                            os.rename(f"{img_directory}/{img}", f"{img_directory}/time_{img[-8:]}")


    return(img_directory)


for conc in os.listdir(alldata):
    for slide in os.listdir(os.path.join(alldata, conc)):
        datatoanalyse = os.path.join(alldata, conc, slide)
        rename(datatoanalyse, extension)

    if not population: # (for each condition/time-lapse experiment)
        import shutil
        # get times as integers (from the current condition/time-lapse condition)
        gettimes = [int(a.split()[0]) for a in os.listdir(os.path.join(alldata, conc))]
        gettimes.sort()
        print(gettimes) #these will only be the integers
        # get first image from the first time point (already renamed to time_0001.{ext})
        first_tp_folder = [a for a in os.listdir(os.path.join(alldata, conc)) if int(a.split()[0])==gettimes[0]][0]
        first_frame_path = os.path.join(os.path.join(alldata, conc), first_tp_folder, f"time_0001.{extension}")

        for slide in os.listdir(os.path.join(alldata, conc)):
            datatoanalyse = os.path.join(alldata, conc, slide)
            print(os.path.join(datatoanalyse, f"time_0001.{extension}"))
            # overwrite current time_0001 frame with time_0001 in first sequence
            try:
                shutil.copy2(first_frame_path, os.path.join(datatoanalyse, f"time_0001.{extension}"))
            except Exception as e:
                print(e)
