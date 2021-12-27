# Here are the libraries I am currently using:
import random

# You are welcome to add any of these:
# import time
# import math
# import random
# import numpy
# import scipy
# import sys

from matts_tree_helpers import get_coords_pixels, FrameManager


def random_fade():
    # NOTE THE LEDS ARE GRB COLOUR (NOT RGB)

    # If you want to have user changeable values, they need to be entered from the command line
    # so import sys and use sys.argv[0] etc.
    # some_value = int(sys.argv[0])

    coords, pixels = get_coords_pixels("coords_2021.csv")

    # YOU CAN EDIT FROM HERE DOWN

    frame_time = 1 / 30
    fade_frame_count = 60

    last_colours = [(0, 0, 0)] * len(coords)

    while True:
        next_colours = [
            tuple(random.randint(0, 255) for _ in range(3)) for _ in range(len(coords))
        ]
        for frame_index in range(fade_frame_count):
            with FrameManager(frame_time):
                lerp = frame_index / fade_frame_count

                # calculate the colour for each pixel
                for i in range(len(coords)):
                    pixels[i] = (
                        min(
                            last_colours[i][0] * (1 - lerp) + next_colours[i][0] * lerp,
                            255.0,
                        ),
                        min(
                            last_colours[i][1] * (1 - lerp) + next_colours[i][1] * lerp,
                            255.0,
                        ),
                        min(
                            last_colours[i][2] * (1 - lerp) + next_colours[i][2] * lerp,
                            255.0,
                        ),
                    )

                # use the show() option as rarely as possible as it takes ages
                # do not use show() each time you change a LED but rather wait until you have changed them all
                pixels.show()

        last_colours = next_colours


if __name__ == "__main__":
    random_fade()
