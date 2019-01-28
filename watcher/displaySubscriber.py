from watcher import subscriber
from cv2 import (
    waitKey,
    namedWindow,
    imshow,
    destroyWindow,
    findContours,
    threshold,
    THRESH_BINARY,
    RETR_EXTERNAL,
    CHAIN_APPROX_SIMPLE,
    createBackgroundSubtractorMOG2,
)


class DisplaySubscriber(subscriber.Subscriber):
    def __init__(self, frame_list, condition):
        subscriber.Subscriber.__init__(self, frame_list, condition)
        self.fg_bg = createBackgroundSubtractorMOG2()

    def background_diff_mog_2(self, image):
        fg_mask = self.fg_bg.apply(image)
        gen_threshold = threshold(fg_mask, 128, 255, THRESH_BINARY)[1]

        return [
            findContours(gen_threshold.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)[1],
            gen_threshold,
        ]


def run(self):
    window_name = "Reactive frame"
    namedWindow(window_name)
    while True:
        self.condition.acquire()
        if len(self.element_list) > 0:
            frame = self.element_list.pop()
            mog_contours, gen_threshold = self.background_diff_mog_2(frame)
            imshow(window_name, frame)
            print("Found {} contours".format(len(mog_contours)))
        else:
            print("No elements to aquire")
        self.condition.release()
        key = waitKey(1) & 0xFF

        if key == ord("q"):
            destroyWindow(window_name)
            break
