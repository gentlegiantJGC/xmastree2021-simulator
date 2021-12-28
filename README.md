# xmastree2021-simulator

## Simulator

This repository contains a simulator for the Neopixel library for those who do not have access to the real hardware.

The simulator is a drop in replacement for the real library. Running your program will bring up the visualiser.

The simulator can generate an animation CSV file from the pixel data given to it.

The following command will run `your_file.py` which contains your code.
After 20 seconds of running (or whatever time you gave as the input) it will exit and create a CSV file containing the frame data which can be run using `run.py` found in the [GSD6338/XmasTree repository](https://github.com/GSD6338/XmasTree/tree/main/03_execution)

`python your_file.py --animation-csv-save-path animation.csv --simulate-seconds 20` - This will simulate and visualise your program for 20 seconds and at the end write a CSV file containing the animation data.

More options and information for the simulator can be found in the [simulator folder](simulator)


## Examples

A number of python source files as well as the baked CSV files can be found in [the examples folder](examples)
