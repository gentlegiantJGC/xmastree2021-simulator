from typing import Iterable, Tuple, List
import sys
from threading import Thread
import argparse
import os
import json
import csv
import atexit
import time

import matplotlib
import matplotlib.pyplot as plt


# without this PyCharm displays it as an image that does not update.
matplotlib.use("TkAgg")
# set the style
plt.style.use("dark_background")

# parser to parse the command line inputs
parser = argparse.ArgumentParser(description="Simulate the neopixel interface.")
parser.add_argument(
    "--coordinates-path",
    dest="coordinates_path",
    type=str,
    help="The path to the coordinate file in txt for csv format. Use this if the code does not set the coordinates.",
)
parser.add_argument(
    "--simulate-seconds",
    dest="simulate_seconds",
    type=float,
    help="Exit after this number of seconds if defined.",
)
parser.add_argument(
    "--animation-csv-save-path",
    dest="animation_csv_save_path",
    type=str,
    help="If defined, will write the values set to an animation CSV file that can be loaded on Matt's tree."
    "Save happens at the end when either sys.exit is called by the code or the UI is closed.",
)
parser.add_argument(
    "--show-delay",
    dest="show_delay",
    type=float,
    help="The amount of time the show method should take to run. "
    "This emulates the behaviour of the real tree. Defaults to 1/60th of a second.",
    default=1 / 60,
)


# Pixel color order constants
RGB = "RGB"
"""Red Green Blue"""
GRB = "GRB"
"""Green Red Blue"""
RGBW = "RGBW"
"""Red Green Blue White"""
GRBW = "GRBW"
"""Green Red Blue White"""


def get_coords(path: str) -> List[Tuple[float, float, float]]:
    """Load the LED coordinates from the file."""
    if not os.path.isfile(path):
        raise ValueError(f"File {path} does not exist.")
    if path.endswith(".txt"):
        with open(path) as f:
            coords = list(map(json.loads, f.readlines()))
    elif path.endswith(".csv"):
        with open(path, "r", encoding="utf-8-sig") as f:
            coords = list(csv.reader(f))
    else:
        raise ValueError(f"Unknown file_format for file {path}")
    coords = [[float(a) for a in c] for c in coords]
    if not all(len(c) == 3 for c in coords):
        raise Exception("Invalid coord format.")
    return coords


class NeoPixel(Thread):
    def __init__(self, _, pixel_count, *, pixel_order: str = "GRB", **kwargs):
        super().__init__()
        self._pixel_count = pixel_count
        if pixel_order == "RGB":
            self._channel_map = (0, 1, 2)
        elif pixel_order == "GRB":
            self._channel_map = (1, 0, 2)
        else:
            raise ValueError("pixel_order must be RGB or GRB")

        # the LED colours
        self._pixels_temp = self._pixels = [(0, 0, 0)] * pixel_count
        # the LED locations
        self._locations = [[0] * pixel_count] * 3
        # have the LED locations been set?
        self._led_init_warn = True

        # Thread variables
        # track if the locations have changed so that the UI thread can update the view
        self._locations_changed = False
        # track if show has been called so the thread can push the changes
        self._show = True
        # True when the thread has finished so we can call sys.exit(0)
        self._exit = False

        # parse the CLI inputs
        parser_args, _ = parser.parse_known_args()
        self._show_delay = parser_args.show_delay
        # Optional argument. The number of seconds to simulate. Exit after this amount of time.
        if parser_args.simulate_seconds is None:
            self._end_time = None
        else:
            self._end_time = time.time() + parser_args.simulate_seconds
        # Optional argument. Path to the coordinates file. Useful if the python script does not set it.
        if parser_args.coordinates_path is not None:
            self.set_pixel_locations(get_coords(parser_args.coordinates_path))
        # Optional argument. The path to save the frame data to at exit.
        self._save_path = parser_args.animation_csv_save_path
        # The stored frame data and times. Only used if animation_csv_save_path CLI option is set
        self._frame_data = []
        self._frame_times = []
        self._last_draw_time = None
        if self._save_path is not None:
            # register the csv save method when python exits
            atexit.register(self._save_animation_csv)

        # start the UI thread
        self.start()

    def set_pixel_locations(self, coords: Iterable[Tuple[float, float, float]]):
        """
        Note that this can be set as a command line input. --coordinates-path [path]
        Custom method to set the location of each pixel.
        This does not exist in the normal neopixel library so you will need to call it like this
        try:
            pixels.set_pixel_locations(coords)
        except AttributeError:
            pass
        """
        coords = list(coords)
        if len(coords) != self._pixel_count:
            raise ValueError(
                "The number of coordinates must equal the number of pixels.\n"
                f"Expected {self._pixel_count} got {len(coords)}"
            )
        if not all(
            len(c) == 3 and all(isinstance(a, (int, float)) for a in c) for c in coords
        ):
            raise ValueError("Coords must be of the form List[Tuple[int, int, int]]")
        self._locations = list(zip(*coords))
        self._locations_changed = True
        self._led_init_warn = False

    @property
    def n(self) -> int:
        """
        The number of neopixels in the chain (read-only)
        """
        return self._pixel_count

    def __setitem__(self, index, color):
        self._pixels_temp[index] = tuple(color[i] / 255.0 for i in self._channel_map)

    def show(self):
        current_time = time.time()
        if self._last_draw_time is not None:
            self._frame_times.append(current_time - self._last_draw_time)
        self._last_draw_time = current_time
        if self._exit:
            sys.exit(0)
        if self._led_init_warn:
            print(
                "The LED locations have not been set. These can be set via the CLI or by calling set_pixel_locations"
            )
        self._pixels = self._pixels_temp.copy()
        self._show = True
        if self._save_path is not None:
            self._frame_data.append(self._pixels)
        if self._show_delay > 0:
            time.sleep(self._show_delay)

    def _save_animation_csv(self):
        with open(self._save_path, "w") as f:
            colour_header_names = ",".join(
                f"{channel}_{led}"
                for led in range(self._pixel_count)
                for channel in "RGB"
            )
            f.write(f"FRAME_TIME,{colour_header_names}\n")
            for frame_time, frame in zip(self._frame_times, self._frame_data):
                colour_data = ",".join(
                    str(min(max(int(col * 255), 0), 255))
                    for led in frame
                    for col in led
                )
                f.write(f"{frame_time*1000},{colour_data}\n")

    def run(self):
        print(
            "You can ignore the errors about threading as long as you are not also using matplotlib."
        )
        # create a figure
        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")

        def exit_(evt):
            self._exit = True

        # exit python when the figure is closed
        fig.canvas.mpl_connect("close_event", exit_)

        while not self._exit:
            if self._show:
                ax.cla()
                ax.scatter(*self._locations, c=self._pixels)
                self._show = False
            if self._locations_changed:
                ax.set_box_aspect([max(ax) - min(ax) for ax in self._locations])
                self._locations_changed = False
            plt.pause(1 / 100_000)
            if self._end_time is not None and time.time() > self._end_time:
                self._exit = True
        plt.close(fig)


if __name__ == "__main__":
    print("Simulator.py is not directly callable. See the readme for usage.")
