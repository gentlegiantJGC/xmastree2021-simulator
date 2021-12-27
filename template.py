# Here are the libraries I am currently using:
import random

# You are welcome to add any of these:
# import time
# import math
# import numpy
# import scipy
# import sys


from matts_tree_helpers import get_coords_pixels, FrameManager


def template():
    # NOTE THE LEDS ARE GRB COLOUR (NOT RGB)

    # If you want to have user changeable values, they need to be entered from the command line
    # so import sys and use sys.argv[0] etc.
    # some_value = int(sys.argv[0])

    coords, pixels = get_coords_pixels("coords_2021.csv")

    # YOU CAN EDIT FROM HERE DOWN

    frame_time = 1 / 30

    while True:
        # This handles waiting if the frame is processed quicker than frame_time
        with FrameManager(frame_time):
            # calculate the colour for each pixel
            for i in range(len(coords)):
                # random colour per LED per frame
                pixels[i] = tuple(random.randint(0, 255) for _ in range(3))

            # use the show() option as rarely as possible as it takes ages
            # do not use show() each time you change a LED but rather wait until you have changed them all
            pixels.show()


if __name__ == "__main__":
    template()
