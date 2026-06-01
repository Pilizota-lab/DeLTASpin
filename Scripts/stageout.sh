#!/bin/bash

#$ -N stageout
#$ -wd "/exports/csce/eddie/biology/groups/pilizota/diana/anaconda/envs/biosensor_analysis/lib/python3.9/site-packages/delta/outputs"
# Hard runtime limit
#$ -l h_rt=24:00:00
#$ -q staging

#provide path to data in submit_analyses.sh as the first parameter in the command line submission
path_on_eddie="$1" #first variable will be the eddie path to slide folder SENSOR_TYPE/DATE/CONC/SLIDE
echo "path on eddie is $path_on_eddie"
slide="$(basename "$path_on_eddie")"
echo $slide
remaining="$(dirname "$path_on_eddie")"
conc="$(basename "$remaining")"
echo $conc
remaining="$(dirname "$remaining")"
date="$(basename "$remaining")"
echo $date
remaining="$(dirname "$remaining")"
sensortype="$(basename "$remaining")"
echo $sensortype

path_on_datastore_results="/exports/csce/datastore/biology/groups/pilizota/biosensors_data/$sensortype/$date/$conc/$slide/"
echo "copying results to datastore starting"
#copy delta_results folder from eddie onto datastore
SOURCE="$path_on_eddie/delta_results/"
# name destination folders differently if single-cell analysis is done
if [ "$3" == "False" ]; then
    DESTINATION="$path_on_datastore_results/delta_results_singlecell/"
else
    DESTINATION="$path_on_datastore_results/delta_results/"
fi


mkdir "$DESTINATION"
rsync -rl "$SOURCE" "$DESTINATION"
echo "copy results on datastore done"

echo "now deleting data from Eddie"
rm -rf "$path_on_eddie"
