import threading
from cv2 import waitKey, namedWindow, imshow, destroyWindow
from time import sleep


class DisplaySubscriber(threading.Thread):
    def __init__(self, frame_queue, condition):
        self.frame_queue = frame_queue
        self.condition = condition
        threading.Thread.__init__(self)

    def run(self):
        window_name = "Reactive frame"
        namedWindow(window_name)
        while True:
            while not self.frame_queue.empty():
                frame = self.frame_queue.get()
                imshow(window_name, frame)
                self.frame_queue.task_done()
            key = waitKey(1) & 0xFF

            if key == ord("q"):
                destroyWindow(window_name)
                break
            sleep(1)
