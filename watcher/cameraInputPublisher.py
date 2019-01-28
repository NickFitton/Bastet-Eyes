from watcher import publisher
from cv2 import VideoCapture


class CameraInputPublisher(publisher.Publisher):
    def __init__(self, frame_list, condition):
        publisher.Publisher.__init__(self, frame_list, condition)
        self.capture_stream = VideoCapture(0)

    def run(self):
        while True:
            ret, frame = self.capture_stream.read()
            if ret:
                self.condition.acquire()
                self.element_list.append(frame)
                self.condition.notify()
                self.condition.release()
