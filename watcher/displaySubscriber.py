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
)
from multiprocessing import Process, Queue


class DisplaySubscriber(subscriber.Subscriber):
    def __init__(self, frame_list, condition, fg_bg):
        subscriber.Subscriber.__init__(self, frame_list, condition)
        self.fg_bg = fg_bg

    def background_diff_mog_2(self, image, queue):
        fg_mask = self.fg_bg.apply(image)
        gen_threshold = threshold(fg_mask, 128, 255, THRESH_BINARY)[1]

        queue.put(
            [
                findContours(gen_threshold.copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)[
                    1
                ],
                gen_threshold,
            ]
        )

    def run(self):
        window_name = "Reactive frame"
        namedWindow(window_name)
        while True:
            self.condition.acquire()
            if len(self.element_list) > 0:
                frame = self.element_list.pop()
                queue = Queue()
                contour_process = Process(
                    target=self.background_diff_mog_2, args=(frame, queue)
                )
                contour_process.start()
                mog_contours, gen_threshold = queue.get()
                contour_process.join()
                imshow(window_name, gen_threshold)
                print("Found {} contours".format(len(mog_contours)))
            self.condition.release()
            key = waitKey(1) & 0xFF

            if key == ord("q"):
                break
        destroyWindow(window_name)
