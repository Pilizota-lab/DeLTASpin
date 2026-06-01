#!/bin/bash

# Grid engine options
#$ -wd "/exports/csce/eddie/biology/groups/pilizota/diana/anaconda/envs/biosensor_analysis/lib/python3.9/site-packages/delta/outputs"
#$ -l h_rt=24:00:00
#$ -l h_vmem=512G
#$ -q gpu 
#$ -pe gpu-a100 1
##$ -l gpu=1
##$ -pe sharedmem 1
#$ -M $(whoami)@ed.ac.uk
#$ -m as 
# email if job is aborted or suspended so I can look into it (will only email if crashes bash script fails, not if python script fails)

slide_to_analyse="$1"

source /etc/profile.d/modules.sh
module load anaconda
# source activate biosensor_analysis
source activate /exports/csce/eddie/biology/groups/pilizota/diana/anaconda/envs/biosensor_analysis

# Check if environment was activated successfully
if [ "$CONDA_DEFAULT_ENV" == "biosensor_analysis" ]; then
        echo "Conda environment activated successfully."
fi

echo $2 
echo $3
echo $4

echo "submitting $slide_to_analyse for analysis"
#job payload
python -u ../delta_for_one.py "$slide_to_analyse" $2 $3 $4

#deactivate conda env
conda deactivate
