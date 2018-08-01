## Description

Using paxer simulation (fax) to generate data from fake input.

## Motivation

Fax is designed to mimic detector responses to photons and electrons at given location. It is already implemented in full chain simulation.

However, full chain simulation is not cost effective timewise when the goal is not being most truthful to physics, instead just wanting to study certain feature of the detector, for example electron diffusion, photon propagation.

The scripts here make up to an isolated module to run fax.

## To Run

### For test run
You will need Xenon1T code to run this, for testing run `python fax_production_main.py`, in it you can edit 
 - `head_directory`: where all the produced files will be stored
 - `default_config`: where you can change the configs
 - `num_group`: of all the jobs you have, how many group do you want them divided into. Each group will be submitted to midway computation node individually.
 - `max_num_submit`: the maximum number of jobs will you allow running on computation nodes under your user name.


### Customize your own production
__One__ In `fax_production_control.py`
 - Under class `Setup`
     - Edit line 49 and 51 to switch between single config and multiple configs, Here the config means fax production configs, not pax configs
     - Edit `_generate_config()`: here you can make copies of default_config and change individual items in it and create a list of configurations you want to run. (All configurations must have differnt names)
 

__Second__ go to `fax_production_process.py`
 - Under class `RunAllProcess` 
     - Edit `__init__()`: comment out or replace inidividual process. The individual process in `process_list` are in the order of execution.
         - Here class `CreateFake` will create fake .csv file from the configuration you generate in setup
         - While class `CreateFakeFromPickle` will require a input from real data minitree 'Corrections' and 'Basics' under the name '{configuration_name}.pkl' in current directory.

 - Under class `BuildMiniTree`
     - Edit `_process()`: add the minitrees you want in hax.minitrees.load()
     - Edit `hax_init`: specify hax.init() conditions

## Thanks to 

Qing and Joey for that most classes in fax_production_process.py are modified from their code
Chris and Sander for that Batch and Submit class in fax_production_control.py are modified from their code
