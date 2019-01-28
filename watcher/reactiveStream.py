from reactive import cameraInputPublisher, displaySubscriber
import threading


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


# file_path = configuration(argv)
frame_buffer = []
frame_condition = threading.Condition()

# inputStreamPublisher = mjpegInputPublisher.InputPublisher(
#     frame_buffer, frame_condition, mjpg_url
# )
inputStreamPublisher = cameraInputPublisher.CameraInputPublisher(
    frame_buffer, frame_condition
)
displayStreamSubscriber = displaySubscriber.DisplaySubscriber(
    frame_buffer, frame_condition
)

inputStreamPublisher.start()
displayStreamSubscriber.start()
