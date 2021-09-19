## Overview

This repo represents a pipeline to compute glicko rankings for a given dataset in csv format.

It's currently set up to work on data from the NAF, the organising body of the board game "Blood Bowl". However, it could be generalised with a little effort.

## Environment

Hopefully simple with `conda` installed. Simply run the `installenv.sh` script. This reads the package dependencies from the `requirements.txt` file.

This repo is also set up with `binder`, allowing anyone to set up an interactive session with these data. Instructions to follow. This is what the `environment.yml` file is for.

## Running

Once conda and the enviroment is set up, the command `snakemake` should create all the necessary files. You can read more about snakemake (here)[]. The main parameters can be changed in the `config.yml` file.

Alternate config `snakemake --configfile config_global.yml`


## Output

The main output file is in `output/player_ranks.csv`, this contains the current rankings.
The pipeline also creates an html output (`rankings.html`) that can be opened by any (I think) browser to sort and filter the data using interactive `bokeh` tables.
Finally, there is an `hdf5` archive that contains all player ranks, including phi and mu, over all ranking periods. This file is much larger!
