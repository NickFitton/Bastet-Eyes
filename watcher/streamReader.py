from threading import Thread
from cv2 import (
    VideoCapture,
    cvtColor,
    COLOR_BGR2GRAY,
    resize,
    createBackgroundSubtractorMOG2,
    threshold,
    THRESH_BINARY,
    RETR_EXTERNAL,
    CHAIN_APPROX_SIMPLE,
    findContours,
    boundingRect,
)
import logging
from watcher.entities import NewEntity


class StreamReader(Thread):
    def __init__(self, frame_queue, terminate_event, stream_url):
        self.frame_queue = frame_queue
        self.term_event = terminate_event
        self.logger = logging.getLogger(__name__)
        Thread.__init__(self, name="Reader", daemon=True)

        self.stream = VideoCapture(stream_url)

    def run(self):
        while not self.term_event.is_set():
            ret, frame = self.stream.read()
            if frame is not None and ret is True:
                self.frame_queue.put(frame)


class FrameProcessor(Thread):
    def __init__(self, frame_queue, processed_frame_queue, terminate_event, scale):
        self.frame_queue = frame_queue
        self.processed_frame_queue = processed_frame_queue
        self.term_event = terminate_event
        self.logger = logging.getLogger(__name__)
        Thread.__init__(self, name="Reader", daemon=True)

        self.scale = scale
        self.fg_bg = createBackgroundSubtractorMOG2()

    def run(self):
        while not self.term_event.is_set():
            if not self.frame_queue.empty():
                original_frame = self.frame_queue.get()
                frame = resize(original_frame, (0, 0), fx=self.scale, fy=self.scale)
                frame = cvtColor(frame, COLOR_BGR2GRAY)
                frame = self.fg_bg.apply(frame)
                frame = threshold(frame, 128, 255, THRESH_BINARY)[1]
                self.processed_frame_queue.put([original_frame, frame])
                self.frame_queue.task_done()


class ContourFinder(Thread):
    def __init__(
        self,
        processed_frame_queue,
        contour_queue,
        terminate_event,
        min_contour_area,
        _id,
    ):
        self.processed_frame_queue = processed_frame_queue
        self.contour_queue = contour_queue
        self.term_event = terminate_event
        self.logger = logging.getLogger(__name__)
        Thread.__init__(self, name="Displayer {}".format(_id), daemon=True)
        self.min_contour_area = min_contour_area

    def run(self):
        while not self.term_event.is_set():
            if not self.processed_frame_queue.empty():
                frame = self.processed_frame_queue.get()
                self.processed_frame_queue.task_done()
                contours = findContours(
                    frame[1].copy(), RETR_EXTERNAL, CHAIN_APPROX_SIMPLE
                )[1]
                entities = []
                for contour in contours:
                    x, y, w, h = boundingRect(contour)
                    if w * h > self.min_contour_area:
                        entities.append(NewEntity(x, y, w, h))

                for e1 in range(0, len(entities)):
                    for e2 in range(e1 + 1, len(entities)):
                        if entities[e2].alive and NewEntity.touching(
                            entities[e1], entities[e2]
                        ):
                            if entities[e1].size() > entities[e1].size():
                                entities[e1].includes(entities[e2])
                                entities[e2].kill()
                            else:
                                entities[e2].includes(entities[e1])
                                entities[e1].kill()

                # for e1 in entities:
                #     for e2 in entities:
                #         if e1 is not e2 and e2.alive and e1.size() > e2.size() and NewEntity.touching(e1, e2):
                #             e1.includes(e2)
                #             e2.kill()

                self.contour_queue.put([entities, frame[0]])
