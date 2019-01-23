from watcher import displaySubscriber, inputPublisher
from sys import argv
import threading
from cv2 import createBackgroundSubtractorMOG2


def configuration(arguments):
    num_args = len(arguments)
    if num_args < 2:
        print("Required arguments:")
        print("-m\tMedia Url")
        exit(0)
    elif (arguments[2] == "-h") | (arguments[2] == "--help"):
        print("Required arguments:")
        print("-m\tMedia Url")
        exit(0)

    media_url = ""

    for i in range(0, num_args):
        if arguments[i] == "-m":
            media_url = arguments[i + 1]

    return media_url


fg_bg = createBackgroundSubtractorMOG2()
mjpg_url = configuration(argv)
frame_buffer = []
frame_condition = threading.Condition()

inputStreamPublisher = inputPublisher.InputPublisher(
    frame_buffer, frame_condition, mjpg_url
)
displayStreamSubscriber = displaySubscriber.DisplaySubscriber(
    frame_buffer, frame_condition, fg_bg
)

inputStreamPublisher.start()
displayStreamSubscriber.start()
