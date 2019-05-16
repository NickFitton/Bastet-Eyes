import cv2
import logging
from sys import argv
from time import time
from math import ceil, floor
from os import getcwd, path, makedirs
import os
import queue
import threading
from picamera.array import PiRGBArray
from picamera import PiCamera

from src.entities import Entity
from src.request import register_with_server, get_access_token
from src.movement import background_diff_mog_2
from src.reactiveReporting import Reporter
from src.frameAnalysis import Analyzer

logging.basicConfig(
    format="[%(threadName)s\t] %(asctime)s - %(levelname)s:\t%(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def save_to_local(image, entry_time, exit_time):
    if not path.exists("/tmp/camera"):
        makedirs("/tmp/camera")
    tmp_entry = floor(entry_time)
    tmp_exit = floor(exit_time)
    cv2.imwrite("/tmp/camera/{}_{}.jpg".format(tmp_entry, tmp_exit), image)


def movement_recognition(existing_entities, new_frame, drawing_frame):
    global fg_bg
    preexisting_entities = existing_entities.copy()
    mog_contours, fg_bg = background_diff_mog_2(new_frame, fg_bg)

    for found_contour in mog_contours:
        if cv2.contourArea(found_contour) >= minContourArea:
            x, y, w, h = cv2.boundingRect(found_contour)
            new_entity = Entity(x, y, new_frame[y : y + h, x : x + w])
            entity_exists = False
            for preexisting_entity in preexisting_entities:
                if (not entity_exists) and preexisting_entity.is_entity(new_entity):
                    preexisting_entity.update(new_entity)
                    entity_exists = True
                    break

            if not entity_exists:
                logger.debug("Adding new entity")
                captured_entities.append(new_entity)

    for existingEntity in captured_entities:
        if time() - existingEntity.last_active > 2:
            logger.debug(
                "Entity '{}' became inactive, reporting".format(existingEntity.id)
            )
            if backend_url == "":
                save_to_local(
                    existingEntity.best_image,
                    existingEntity.first_active,
                    existingEntity.last_active,
                )
            else:
                reporting_queue.put(existingEntity)
            captured_entities.remove(existingEntity)
        else:
            cv2.rectangle(
                drawing_frame,
                (existingEntity.x, existingEntity.y),
                (
                    existingEntity.x + existingEntity.image.shape[1],
                    existingEntity.y + existingEntity.image.shape[0],
                ),
                (existingEntity.b, existingEntity.g, existingEntity.r),
                2,
            )


def configuration(arguments):
    num_args = len(arguments)
    if num_args < 2 or ((arguments[2] == "-h") | (arguments[2] == "--help")):
        print("Optional arguments:")
        print("-s\tServer Url")
        print("-c\tMinimum Contour")
        print("--scale\tStream scale")
        exit(0)

    server_url = ""
    contour = 3000
    scale = 1

    for i in range(0, num_args):
        if arguments[i] == "-s":
            server_url = arguments[i + 1]
        elif arguments[i] == "-c":
            contour = int(arguments[i + 1])
        elif arguments[i] == "--scale":
            scale = float(arguments[i + 1])
    return server_url, contour, scale


backend_url, minContourArea, video_scale = configuration(argv)
stats_dir = "/tmp/stats"
stats_file_name = str(time())
current_path = getcwd()

if not os.path.isdir(stats_dir):
    os.mkdir(stats_dir)

stats_file = open(os.path.join(stats_dir, stats_file_name), "a+")

fg_bg = cv2.createBackgroundSubtractorMOG2()
new_id, new_password = register_with_server(backend_url)
token = get_access_token(backend_url, new_id, new_password)

captured_entities = []
reporting_queue = queue.Queue()
frame_queue = queue.Queue()
terminate_reporting = threading.Event()
frame_analyser = Analyzer(
    frame_queue, reporting_queue, terminate_reporting, minContourArea
)
movement_reporter = Reporter(
    reporting_queue,
    terminate_reporting,
    backend_url,
    token,
    tmp_location="/tmp/src",
)
frame_analyser.start()
movement_reporter.start()

interval_sec = 10
frame_count = 0
last_check = time()
logger.info("Setup complete, recording at scale {}".format(video_scale))

camera = PiCamera()
camera.resolution = (1280, 720)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(1280, 720))
for rawCapture in camera.capture_continuous(
    rawCapture, format="bgr", use_video_port=True
):
    frame = rawCapture.array
    if frame is not None:
        frame_count += 1
        if video_scale != 1:
            small_frame = cv2.resize(frame, (0, 0), fx=video_scale, fy=video_scale)
        else:
            small_frame = frame.copy()
        # movement_recognition(captured_entities, small_frame, drawing_frame)
        frame_queue.put(small_frame)
    rawCapture.truncate(0)
    key = cv2.waitKey(1) & 0xFF

    frame_time = time()
    if frame_time - last_check > interval_sec:
        if frame_count == 0:
            logger.warning(
                "Shutting down, no frames received in past {} seconds".format(
                    interval_sec
                )
            )
            terminate_reporting.set()
        logger.info("FPS: {}".format(ceil(frame_count / interval_sec)))
        last_check = frame_time
        frame_count = 0

logger.info("Complete")
stats_file.close()
