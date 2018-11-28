from os import getcwd, remove, path, makedirs

from math import floor
from time import time
import cv2
import requests
import sys

from entities import Entity


def log(line):
    print("[{}]:\t{}".format(floor(time()), line))


def background_diff_mog_2(image):
    fg_mask = fgbg.apply(image)
    threshold = cv2.threshold(fg_mask, 128, 255, cv2.THRESH_BINARY)[1]
    cv2.imshow('mog_threshold', threshold)
    return cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]


def save_to_server(image, entry_time, exit_time, image_time):
    metadata = {'entryTime': str(entry_time), 'exitTime': str(exit_time), 'imageTime': str(image_time)}
    image_id = requests.post('{}:8080/image'.format(backend_url), json=metadata).json()["id"]

    file_location = "{}.jpg".format(image_id)

    cv2.imwrite(file_location, image)

    imagefile = {'file': open(file_location, 'rb')}
    response = requests.patch('{}:8080/image/{}'.format(backend_url, image_id), files=imagefile)
    if response.status_code == 202:
        remove(file_location)
        log("Image uploaded successfully, removed from local storage")
    else:
        log("Persisting image locally due to failure of connection with server")


def save_to_local(image, entry_time, exit_time):
    if not path.exists("/tmp/camera"):
        makedirs("/tmp/camera")
    tmp_entry = floor(entry_time)
    tmp_exit = floor(exit_time)
    cv2.imwrite("/tmp/camera/{}_{}.jpg".format(tmp_entry, tmp_exit), image)


def movement_recognition(existing_entities, new_frame):
    preexisting_entities = existing_entities.copy()
    mog_contours = background_diff_mog_2(new_frame)

    for found_contour in mog_contours:
        if cv2.contourArea(found_contour) >= minContourArea:
            x, y, w, h = cv2.boundingRect(found_contour)
            new_entity = Entity(x, y, original_frame[y:y + h, x:x + w])
            entity_exists = False
            for preexisting_entity in preexisting_entities:
                if (not entity_exists) and preexisting_entity.is_entity(new_entity):
                    preexisting_entity.update(new_entity)
                    entity_exists = True
                    break

            if not entity_exists:
                log("Adding new entity")
                captured_entities.append(new_entity)

    for existingEntity in captured_entities:
        if time() - existingEntity.last_active > 2:
            log("Entity '{}' became inactive, reporting".format(existingEntity.id))
            if backend_url == "":
                save_to_local(existingEntity.best_image, existingEntity.first_active, existingEntity.last_active)
            else:
                save_to_server(existingEntity.best_image, existingEntity.first_active, existingEntity.last_active,
                               existingEntity.image_time)
            captured_entities.remove(existingEntity)
        else:
            cv2.rectangle(frame,
                          (existingEntity.x, existingEntity.y),
                          (existingEntity.x + existingEntity.image.shape[1],
                           existingEntity.y + existingEntity.image.shape[0]),
                          (existingEntity.b, existingEntity.g, existingEntity.r), 2)


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


backend_url, mjpg_url, minContourArea = configuration(sys.argv)
current_path = getcwd()
log(current_path)
initialization_time = floor(time())

fgbg = cv2.createBackgroundSubtractorMOG2()

captured_entities = []

log("Setup complete, recording")

cap = cv2.VideoCapture(mjpg_url)
while True:
    ret, frame = cap.read()
    original_frame = frame.copy()

    movement_recognition(captured_entities, frame)

    cv2.imshow('Video', frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    elif key == ord("r"):
        captured_entities = []
