from os import getcwd, remove

from picamera.array import PiRGBArray
from picamera import PiCamera
from math import floor
from time import time
import cv2
import requests

from entities import Entity


def log(line):
    print("[{}]:\t{}".format(floor(time()), line))


log("Setting up")
current_path = getcwd()
initialization_time = floor(time())

fgbg = cv2.createBackgroundSubtractorMOG2()
camera = PiCamera()
camera.resolution = (1640, 1232)
camera.framerate = 32
camera.rotation = 180
rawCapture = PiRGBArray(camera)

minContourArea = 6000
captured_entities = []

log("Setup complete, recording")


def background_diff_mog_2(image):
    fg_mask = fgbg.apply(image)
    threshold = cv2.threshold(fg_mask, 128, 255, cv2.THRESH_BINARY)[1]
    return cv2.findContours(
        threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[1]


def save_to_server(image, entry_time, exit_time, image_time):
    metadata = {
        "entryTime": str(entry_time),
        "exitTime": str(exit_time),
        "imageTime": str(image_time),
    }
    image_id = requests.post("http://192.168.0.28:8080/image", json=metadata).json()[
        "id"
    ]
    print(image_id)

    file_location = "{}.jpg".format(image_id)

    cv2.imwrite(file_location, image)

    imagefile = {"file": open(file_location, "rb")}
    response = requests.patch(
        "http://192.168.0.28:8080/image/{}".format(image_id), files=imagefile
    )
    if response.status_code == 202:
        remove(file_location)
        log("Image uploaded successfully, removed from local storage")
    else:
        log("Persisting image locally due to failure of connection with server")


def save_to_local(image, entry_time, exit_time):
    cv2.imwrite("{}/{}.jpg".format(entry_time, exit_time), image)


start_time = time()
for rawCapture in camera.capture_continuous(
    rawCapture, format="bgr", use_video_port=True
):
    frame = rawCapture.array
    original_frame = frame.copy()

    preexisting_entities = captured_entities.copy()
    mog_contours = background_diff_mog_2(frame)

    for found_contour in mog_contours:
        if cv2.contourArea(found_contour) >= minContourArea:
            x, y, w, h = cv2.boundingRect(found_contour)
            newEntity = Entity(x, y, original_frame[y : y + h, x : x + w])
            entity_exists = False
            for preexisting_entity in preexisting_entities:
                if (not entity_exists) and preexisting_entity.is_entity(newEntity):
                    preexisting_entity.update(newEntity)
                    entity_exists = True
                    break

            if not entity_exists:
                log("Adding new entity")
                captured_entities.append(newEntity)

    for existingEntity in captured_entities:
        if time() - existingEntity.last_active > 5:
            log("Entity '{}' became inactive, reporting".format(existingEntity.id))
            save_to_server(
                existingEntity.best_image,
                existingEntity.first_active,
                existingEntity.last_active,
                existingEntity.image_time,
            )
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

    rawCapture.truncate(0)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break
    elif key == ord("r"):
        captured_entities = []
