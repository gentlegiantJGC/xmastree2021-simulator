from typing import Iterable, Tuple, List, Optional
import sys
import argparse
import os
import json
import csv
import atexit
import time

from multiprocessing import Process, Queue
import queue

import matplotlib
import matplotlib.pyplot as plt


# without this PyCharm displays it as an image that does not update.
matplotlib.use("TkAgg")
# set the style
plt.style.use("dark_background")


def get_parser():
    # parser to parse the command line inputs
    parser = argparse.ArgumentParser(description="Simulate the neopixel interface.")
    parser.add_argument(
        "--coordinates-path",
        dest="coordinates_path",
        type=str,
        help="The path to the coordinate file in txt for csv format. "
             "Use this if the code does not set the coordinates.",
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
        default=0,
    )
    parser.add_argument(
        "--no-gui",
        dest="gui",
        action="store_false",
        help="If true will show the GUI.",
        default=True,
    )
    return parser


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


class Exit:
    pass


class Locations(list):
    pass


class Pixels(list):
    pass


def matplotlib_process(command_queue: Queue):
    """Run matplotlib in a new process."""
    # create a figure
    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")

    run = True

    def exit_process(evt):
        nonlocal run
        run = False

    # exit python when the figure is closed
    fig.canvas.mpl_connect("close_event", exit_process)

    pixels_changed = False
    pixels = None
    locations_changed = False
    locations = None

    while run:
        while True:
            try:
                command = command_queue.get_nowait()
            except queue.Empty:
                break
            else:
                if isinstance(command, Exit):
                    run = False
                    break
                elif isinstance(command, Locations):
                    locations_changed = True
                    locations = command
                elif isinstance(command, Pixels):
                    pixels_changed = True
                    pixels = command
                else:
                    print(command)

        if locations_changed:
            ax.set_box_aspect([max(ax) - min(ax) for ax in locations])
            locations_changed = False
        if pixels_changed:
            if locations is None:
                print(
                    "The LED locations have not been set. "
                    "These can be set via the CLI or by calling set_pixel_locations"
                )
            else:
                ax.cla()
                ax.scatter(*locations, c=pixels)
                pixels_changed = False

        plt.pause(1 / 100_000)
    plt.close(fig)


class NeoPixel:
    _pixel_count: int  # The number of pixels the devices has
    _channel_map: Tuple[int, int, int]  # RGB indexes

    _process: Optional[Process]  # The matplotlib process
    _process_queue: Optional[Queue]  # A Queue used to send data to the matplotlib process

    def __init__(self, _, pixel_count: int, *, pixel_order: str = "GRB", **kwargs):
        super().__init__()
        self._pixel_count = pixel_count
        if pixel_order == "RGB":
            self._channel_map = (0, 1, 2)
        elif pixel_order == "GRB":
            self._channel_map = (1, 0, 2)
        else:
            raise ValueError("pixel_order must be RGB or GRB")

        # the LED colours
        self._pixels = [(0, 0, 0)] * pixel_count

        # parse the CLI inputs
        parser_args, _ = get_parser().parse_known_args()

        # The delay time used in the show method
        self._show_delay = parser_args.show_delay

        # Optional argument. The path to save the frame data to at exit.
        self._save_path = parser_args.animation_csv_save_path
        # The stored frame data and times. Only used if animation_csv_save_path CLI option is set
        self._frame_data = []
        self._frame_times = []
        self._last_draw_time = None

        # Set up the animation save if requested
        if self._save_path is not None:
            # register the csv save method when python exits
            atexit.register(self._save_animation_csv)

        # Enable the GUI if required
        self._gui = parser_args.gui
        if self._gui:
            # start the UI thread
            self._process_queue = Queue()
            self._process = Process(target=matplotlib_process, args=(self._process_queue,))
            self._process.start()
        else:
            self._process_queue = None
            self._process = None
            print("Running in no GUI mode.")

        # Optional argument. Path to the coordinates file. Useful if the python script does not set it.
        if parser_args.coordinates_path is not None:
            self.set_pixel_locations(get_coords(parser_args.coordinates_path))

        # Optional argument. The number of seconds to simulate. Exit after this amount of time.
        if parser_args.simulate_seconds is not None:
            self._end_time = time.perf_counter() + parser_args.simulate_seconds
        else:
            self._end_time = None

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
        if self._process_queue is not None:
            self._process_queue.put_nowait(Locations(zip(*coords)))

    @property
    def n(self) -> int:
        """
        The number of neopixels in the chain (read-only)
        """
        return self._pixel_count

    def __setitem__(self, index, color):
        self._pixels[index] = tuple(color[i] / 255.0 for i in self._channel_map)

    def show(self):
        current_time = time.perf_counter()

        # check if we should exit
        if self._end_time is not None and current_time > self._end_time:
            if self._process is not None:
                if self._process.is_alive():
                    # if the matplotlib process is running then kill it
                    self._process_queue.put_nowait(Exit())
                    self._process.join()
            sys.exit(0)
        elif self._process is not None and not self._process.is_alive():
            # The matplotlib process has exited. We should exit.
            if self._save_path is not None:
                # There is an issue where if the process is exited it will get stuck. This fixes it.
                atexit.unregister(self._save_animation_csv)
                self._save_animation_csv()
            # There is sometimes an error that gets printed to the console. I am not sure how to fix this
            # https://stackoverflow.com/questions/26692284/how-to-prevent-brokenpipeerror-when-doing-a-flush-in-python
            sys.stderr.close()
            sys.exit(0)

        # update the save data if we are storing that.
        if self._save_path is not None:
            # update the frame times
            if self._last_draw_time is not None:
                self._frame_times.append(current_time - self._last_draw_time)
            self._last_draw_time = current_time
            # update the frame data
            self._frame_data.append(self._pixels.copy())

        # give the pixel data to the process
        if self._process_queue is not None:
            self._process_queue.put_nowait(Pixels(self._pixels))

        # sleep if required
        end_time = current_time + self._show_delay
        while time.perf_counter() < end_time:
            # time.sleep has inaccuracies on some platforms
            pass

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
                f.write(f"{round(frame_time*1000, 3)},{colour_data}\n")


if __name__ == "__main__":
    print("Simulator.py is not directly callable. See the readme for usage.")
