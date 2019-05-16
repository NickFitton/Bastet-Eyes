from threading import Thread
import cv2
from time import sleep
import logging
from src.entities import Entity
from time import time


class Analyzer(Thread):
    # Initialization of the reporter thread, loads with everything it needs to communicate with the server
    def __init__(self, frame_queue, report_queue, terminate_event, min_contour_area):
        self.frame_queue = frame_queue
        self.report_queue = report_queue
        self.term_event = terminate_event
        self.logger = logging.getLogger(__name__)
        # self.window_name = "MOG Frame"
        Thread.__init__(self, name="Analyzer", daemon=True)

        self.fg_bg = cv2.createBackgroundSubtractorMOG2()
        self.min_contour_area = min_contour_area
        self.captured_entities = []

    def background_diff_mog_2(self, image):
        fg_mask = self.fg_bg.apply(image)
        threshold = cv2.threshold(fg_mask, 128, 255, cv2.THRESH_BINARY)[1]
        return cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    def movement_recognition(self, new_frame):
        preexisting_entities = self.captured_entities.copy()
        mog_contours = self.background_diff_mog_2(new_frame)
        for found_contour in mog_contours:
            area = cv2.contourArea(found_contour)
            if area >= self.min_contour_area:
                x, y, w, h = cv2.boundingRect(found_contour)
                new_entity = Entity(x, y, new_frame[y: y + h, x: x + w])
                entity_exists = False
                for preexisting_entity in preexisting_entities:
                    if (not entity_exists) and preexisting_entity.is_entity(new_entity):
                        preexisting_entity.update(new_entity)
                        entity_exists = True
                        break

                if not entity_exists:
                    self.logger.debug("Adding new entity")
                    self.captured_entities.append(new_entity)

        for existingEntity in self.captured_entities:
            if time() - existingEntity.last_active > 2:
                self.logger.debug(
                    "Entity '{}' became inactive, reporting".format(existingEntity.id)
                )
                self.report_queue.put(existingEntity)
                self.captured_entities.remove(existingEntity)

    def run(self):
        # cv2.namedWindow(self.window_name)
        while not self.term_event.is_set():
            while not self.frame_queue.empty():
                frame = self.frame_queue.get()

                self.movement_recognition(frame)

                self.frame_queue.task_done()
            sleep(1)
        # cv2.destroyWindow(self.window_name)
