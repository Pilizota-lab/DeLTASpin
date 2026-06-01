# HPC scripts

This folder contains example bash scripts used to run DeLTASpin on the Eddie (Edinburgh University's HPC cluster). 

These scripts were written for the Eddie cluster configuration used in our group (last checked on **May 2026**). They include cluster-specific paths, scheduler settings, environment names, and data-staging steps. Users running DeLTASpin on a different system need to adapt these settings before use.

The scripts are provided to document the workflow used for large image-sequence analysis on a high-performance computing cluster. They are not intended to be fully portable without modification.

## Files

* `analysis.sh` – example analysis script for running the DeLTASpin pipeline.
* `new_master_script.sh` – example master script for submitting or coordinating analysis jobs.
* `stagein.sh` – example script for staging input data onto the cluster.
* `stageout.sh` – example script for copying results back after analysis.
