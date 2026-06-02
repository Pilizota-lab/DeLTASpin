#!/bin/bash

#this is the master script which:
#1. stages data data server -> cluster (stagein.sh)
#2. rename files on cluster as time_04d.{ext} format (and move files if needed - i.e., if pop=False)
#3. analyse data on cluster (analysis.sh, submitted in iteratively through submit_analyses.sh)
#4. stage data cluster -> data server (stageout.sh)
# this only works when data is organised in two hierarchic levels (folders with data in folders in a big folder) - adjust for other cases

# note submitting this script can take between 1 and 4 arguments:
# $1 represents the relative path to the dataset (e.g., biosensor_type/date; required argument, no default)
# $2 represents extension (string type) - given by file format (by defauly, tif)
# $3 represents population (boolean type) - False for single-cell analysis over time sequences (by default, True)
# $4 represents frame rate (int) - for motor speed adjustment (by default, 100 fps)

# Expected input structure:
# DATA_ROOT/
# └── sensor_type/
#     └── date/
#         └── concentration/
#             └── slide/
#                 └── sequence/


# extra arguments: file extension of data sets (.tif by default) and population (T by default) 
ext="tif"
pop="True"
fps="100"

for arg in "$@"; do
        case $arg in
                extension=*) #check if argument starts with "extension=" ")" terminates pattern
                        ext="${arg#*=}";;
                population=*) #check if argument starts with "population="
                        pop="${arg#*=}";;
                framerate=*) #check if argument starts with "framerate="
                        fps="${arg#*=}";;
                *) # unrecognised patterns
                        echo "Unknown argument: $arg"
                        ;;

        esac
done



#1. stagein 
qsub stagein.sh "$1" "$ext" "$pop" "$fps" 
sleep 15 # in rare cases, the job is searched for before being submitted

check_status() {
        qstat -u $(whoami) | grep "stagein"
}

job_running=1

while [ $job_running -eq 1 ]; do
    if check_status; then
        echo "Stagein is still running. Checking again in 30 seconds."
        sleep 30 # 0.5 minutes in seconds
    else
        echo "stagein is done or not found."
        job_running=0
    fi
done

dataset_name="$1"
path_to_data="{DATA_ROOT}/${dataset_name}"
echo "$path_to_data"

#2. submit analyses

for concentration in "$path_to_data"/*; do
    conc=$(basename "$concentration")
	if [ "$conc" != "Thumbs.db" ]; then
		for slide in "$concentration"/*; do
			#give executable permissions to files
			for frame in "$slide"/*; do
					chmod +rwx "$frame"
			done
			sli=$(basename "$slide")
			if [ "$sli" != "Thumbs.db" ]; then 
				#ANALYSIS SHOULD NOT BE HELD
						qsub -N analysis_"$conc"_"$sli" analysis.sh "$slide" $ext $pop $fps
						#3.stageout - wait until "slide" has been analysed (or crashed)
						qsub -hold_jid analysis_"$conc"_"$sli" stageout.sh "$slide" $ext $pop $fps
			fi
		done
	fi
done

