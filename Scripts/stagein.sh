#!/bin/bash

#$ -N stagein
#$ -wd "/exports/csce/eddie/biology/groups/pilizota/diana/anaconda/envs/biosensor_analysis/lib/python3.9/site-packages/delta/outputs"
# Hard runtime limit
#$ -l h_rt=24:00:00
#$ -q staging

path_to_folder="/exports/csce/datastore/biology/groups/pilizota/biosensors_data/$1"
data_date="$(basename "$1")"

echo "staging started"
# find in which sensor file data should be placed
remaining="$(dirname "$path_to_folder")"
sensortype="$(basename "$remaining")"
echo $sensortype

SOURCE=$path_to_folder # on datastore
# make destination directory if missing 
mkdir "/exports/eddie/scratch/$(whoami)/biosensor_data/"
mkdir "/exports/eddie/scratch/$(whoami)/biosensor_data/$sensortype/"
DESTINATION="/exports/eddie/scratch/$(whoami)/biosensor_data/$sensortype/" # on the group's space on Eddie
rsync -rl "$SOURCE" "$DESTINATION"
echo "staging done"
destination_date="$DESTINATION/$data_date"

# rename files in the time_04d.{ext} format
python -u ../rename.py "$destination_date" "$2" "$3" "$4"
