"""
This is a helper library to minimise code duplication of the setup code and make users code much simpler
"""

from typing import List, Tuple
import json  # used to parse the coordinates
import time  # used to get the current time and sleep
import os
import csv

import board
import neopixel


def get_coords_pixels(path: str):
    """
    Load the coordinates and create the neopixel interface.
    If the file ends .txt it is assumed to be in 2020 format with one json format list containing three floats per line.
    If the file ends .csv it is loaded as a normal csv file with no column names
    """
    coords = get_coords(path)
    return coords, get_neopixel_interface(coords)


def get_neopixel_interface(coords):
    # set up the pixels (AKA 'LEDs')
    pixels = neopixel.NeoPixel(board.D18, len(coords), auto_write=False)
    try:
        pixels.set_pixel_locations(coords)
    except AttributeError:
        pass
    return pixels


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


class FrameManager:
    """
    A class to help cap the frame rate. You shouldn't rely on the neopixel show method having a known delay.
    Use it like this

    with FrameManager(frame_time):  # frame_time should be something like 1/30 to get 30fps
        print("your frame code here")

    See template.py for a more full example.
    """

    def __init__(self, frame_time: float):
        self._frame_time = frame_time
        self._end_time = 0

    def __enter__(self):
        self._end_time = time.perf_counter() + self._frame_time

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If the frame was processed in less time than frame_time then sleep for a bit
        while time.perf_counter() < self._end_time:
            time.sleep(0)


if __name__ == "__main__":
    print("matts_tree_helpers.py is not directly callable. Import it from your code.")
