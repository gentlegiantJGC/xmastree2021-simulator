# Neopixel Simulator, Visualiser and CSV Animation generator

This is a visualiser for the neopixel library for those that just want to simulate the code.
It is a drop-in replacement for the normal library.
Simply put board.py and neopixel.py in the root directory (or add this folder to your path) and you should be good to go.
Note that due to import order this will take preference over the real library. Remove these files if you want to run it with the real library.

Based on the simulator by DutChen18. Source: https://github.com/standupmaths/xmastree2020/pull/5/files

Changes:
- Moves the matplotlib code to a new thread so that the updating code does not block the UI.
- Adds a method to set the pixel locations so that they are not hard coded.
- Made the axis proportional in size.
- Split the code up into two modules so the imports do not need to be modified.
- Added a CLI input to set the pixel locations if they are not set by the code.
- Added a CLI input to set the time the simulation will run for.
- Added a CLI input to generate an animation CSV file which will produce the same result as the code when run.

Potential future work:
Consider adding support for pixel colour order.
Unsure if the one Matt is running uses this

##Usage

### Import
```py
# Import it and use it like you would normally
import board
import neopixel
```

### Create the neopixel interface
```py
# construct the neopixel interface in the normal way
pixels = neopixel.NeoPixel(
    board.D18, len(coords), auto_write=False
)
```

### Set the LED locations
This can be done in one of two ways. You can give the path to the coords file via the CLI option `--coordinates-path [path]` or you can set it via code.

```py
# This is a custom method that does not exist in the real library.
# Call it like this to catch and ignore the error if run on the real hardware.
try:
    pixels.set_pixel_locations(coords)
except AttributeError:
    pass
```

### Command Line Inputs
`--coordinates-path [str]` - If defined will load the coordinates from the file and use them to set the LED locations.

`--simulate-seconds [float]` - If defined will stop simulating after this amount of time. Useful to generate animation csv files of a known time length without modifying the code. 

`--animation-csv-save-path [str]` - If defined will store the frame time and LED colours for each frame and when the program exits will save them to a csv file that can be run.


### Command examples

`python your_file.py --coordinates-path coords_2021.csv` - This will run your program and visualise the output. It will load the coordinates from `coords_2021.csv`

`python your_file.py --animation-csv-save-path animation.csv --simulate-seconds 20` - This will simulate and visualise your program for 20 seconds and at the end write a CSV file containing the animation data.
