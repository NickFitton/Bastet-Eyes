from os import makedirs, path
from cv2 import imwrite
from math import floor


def save_to_local(image, entry_time, exit_time):
    if not path.exists("/tmp/camera"):
        makedirs("/tmp/camera")
    tmp_entry = floor(entry_time)
    tmp_exit = floor(exit_time)
    imwrite("/tmp/camera/{}_{}.jpg".format(tmp_entry, tmp_exit), image)
