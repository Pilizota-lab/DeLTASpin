# HPC scripts

This folder contains the bash scripts used to run DeLTASpin on the Eddie (Edinburgh University's HPC cluster), which uses the AGE batch system. Note that these are specific to the Eddie cluster configuration as of November 2023 (last checked May 2026). Thus, these scripts will need to be adapted if used on a different systems, but are provided as an example. 

## Files
* `stagein.sh` – script for staging data on cluster (server -> cluster)
* `analysis.sh` – script for running the DeLTASpin pipeline 
* `stageout.sh` – script for copying results to permanent storage (cluster -> server)
* `new_master_script.sh` – master script submitting and coordinating the 3 steps above
