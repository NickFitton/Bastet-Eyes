import cv2
import logging
from sys import argv
from time import time
from math import floor
from os import getcwd, path, makedirs
import os

from watcher.entities import Entity, Statistic
from watcher.request import register_with_server, get_access_token, add_motion
from watcher.movement import background_diff_mog_2

logging.basicConfig(
    format="%(asctime)s - %(levelname)s:\t%(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def save_to_local(image, entry_time, exit_time):
    if not path.exists("/tmp/camera"):
        makedirs("/tmp/camera")
    tmp_entry = floor(entry_time)
    tmp_exit = floor(exit_time)
    cv2.imwrite("/tmp/camera/{}_{}.jpg".format(tmp_entry, tmp_exit), image)


def movement_recognition(existing_entities, new_frame, stat):
    global fg_bg
    preexisting_entities = existing_entities.copy()
    mog_contours, fg_bg = background_diff_mog_2(new_frame, fg_bg)
    stat.add_time()

    for found_contour in mog_contours:
        if cv2.contourArea(found_contour) >= minContourArea:
            x, y, w, h = cv2.boundingRect(found_contour)
            new_entity = Entity(x, y, original_frame[y : y + h, x : x + w])
            entity_exists = False
            for preexisting_entity in preexisting_entities:
                if (not entity_exists) and preexisting_entity.is_entity(new_entity):
                    preexisting_entity.update(new_entity)
                    entity_exists = True
                    break

            if not entity_exists:
                logger.debug("Adding new entity")
                captured_entities.append(new_entity)

    stat.add_time()
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
                add_motion(backend_url, token, existingEntity)
            captured_entities.remove(existingEntity)
        else:
            cv2.rectangle(
                frame,
                (existingEntity.x, existingEntity.y),
                (
                    existingEntity.x + existingEntity.image.shape[1],
                    existingEntity.y + existingEntity.image.shape[0],
                ),
                (existingEntity.b, existingEntity.g, existingEntity.r),
                2,
            )
    stat.add_time()


def configuration(arguments):
    num_args = len(arguments)
    if num_args < 2:
        print("Required arguments:")
        print("-m\tMedia Url")
        print("Optional arguments:")
        print("-s\tServer Url")
        print("-c\tMinimum Contour")
        exit(0)
    elif (arguments[2] == "-h") | (arguments[2] == "--help"):
        print("Required arguments:")
        print("-m\tMedia Url")
        print("Optional arguments:")
        print("-s\tServer Url")
        print("-c\tMinimum Contour")
        exit(0)

    server_url = ""
    media_url = ""
    contour = 3000

    for i in range(0, num_args):
        if arguments[i] == "-s":
            server_url = arguments[i + 1]
        elif arguments[i] == "-m":
            media_url = arguments[i + 1]
        elif arguments[i] == "-c":
            contour = int(arguments[i + 1])

    if media_url == "":
        print("Media url must be supplied")
        exit(1)

    return server_url, media_url, contour


backend_url, mjpg_url, minContourArea = configuration(argv)
stats_dir = "/tmp/stats"
stats_file_name = str(time())
current_path = getcwd()


if not os.path.isdir(stats_dir):
    os.mkdir(stats_dir)

stats_file = open(os.path.join(stats_dir, stats_file_name), "a+")

try:
    new_id, new_password = register_with_server(backend_url)
    token = get_access_token(backend_url, new_id, new_password)
except ConnectionError as e:
    logger.error(e)
logger.info("Starting")
fg_bg = cv2.createBackgroundSubtractorMOG2()
first_loop = True

captured_entities = []

logger.info("Setup complete, recording")

cap = cv2.VideoCapture(mjpg_url)
while True:
    stat = Statistic()
    ret, frame = cap.read()
    stat.add_time()
    original_frame = frame.copy()

    stat.add_time()
    movement_recognition(captured_entities, frame, stat)

    stat.set_count(len(captured_entities))

    if first_loop:
        first_loop = False
        headers = "count,start"
        times = len(stat.interim_times)
        for num in range(times):
            headers += ",{}".format(num + 1)
        headers += "\n"
        stats_file.write(headers)
    stats_file.write(stat.print_line())

    cv2.imshow("Video", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    elif key == ord("r"):
        captured_entities = []

stats_file.close()
