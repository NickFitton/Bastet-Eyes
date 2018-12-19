import requests
import logging
import random
import string
import os
import base64
from cv2 import imwrite
import cv2
from watcher.entities import Entity
from requests.exceptions import InvalidSchema

logging.basicConfig(
    format="%(asctime)s - %(levelname)s:\t%(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
data_location = "/tmp/watcher"
credentials_file_name = "credentials.csv"
token_file_name = "token.csv"


def __generate_password():
    return "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(20)
    )


def __save(file_name, line):
    if not os.path.isdir(data_location):
        os.mkdir(data_location)
    with open(os.path.join(data_location, file_name), "w+") as file:
        file.write(line)


def __load(file_name):
    with open(os.path.join(data_location, file_name), "r") as file:
        return file.read()


def __exists(file_name):
    return os.path.isfile(os.path.join(data_location, file_name))


def __save_credentials(camera_id, password):
    __save(credentials_file_name, "{},{}".format(camera_id, password))


def __load_credentials():
    return __load(credentials_file_name).split(",")


def __credentials_exist():
    return __exists(credentials_file_name)


def __save_token(_token):
    __save(token_file_name, _token)


def __load_token():
    return __load(token_file_name)


def __token_exist():
    return __exists(token_file_name)


def __parse_response(response, expected_status_code):
    json = response.json()
    if not response.status_code == expected_status_code:
        logger.error(
            "Server returned bad request with status {}".format(response.status_code)
        )
        if "error" in json:
            raise ConnectionError(
                "Bad communication with server[status={}, error={}}".format(
                    response.status_code, json["error"]
                )
            )
        else:
            raise ConnectionError(
                "Bad communication with server[status={}]".format(response.status_code)
            )
    if "error" in json:
        raise ConnectionError(
            "Bad communication with server[status={}, error={}]".format(
                response.status_code, json["error"]
            )
        )
    elif "data" in json:
        return json["data"]
    else:
        raise ConnectionError(
            "Bad communication with server[status={}, body={}]".format(
                response.status_code, json
            )
        )


def register_with_server(server_url):
    if __credentials_exist():
        logger.debug("Loading previously saved credentials")
        return __load_credentials()

    password = __generate_password()
    body = {"password": password}

    try:
        response = requests.post("{}/v1/cameras".format(server_url), json=body)
        data = __parse_response(response, 201)
        __save_credentials(data["id"], password)
        return data["id"], password
    except InvalidSchema:
        raise ConnectionError("Failed to connect to server")


def get_access_token(server_url, camera_id, password):
    if __token_exist():
        logger.debug("Loading previously saved token")
        return __load_token()

    auth_combo = base64.b64encode(
        "{}:{}".format(camera_id, password).encode("utf-8")
    ).decode("utf-8")
    auth_header = "Basic {}".format(auth_combo)
    logger.info(auth_header)
    headers = {"authorization": auth_header}

    try:
        response = requests.post(
            "{}/v1/login/camera".format(server_url), headers=headers
        )
        new_token = __parse_response(response, 200)
        __save_token(new_token)
        logger.info(new_token)
    except InvalidSchema:
        raise ConnectionError("Failed to connect to server")


def add_motion(server_url, auth_token, new_entity):
    metadata = {
        "entryTime": str(new_entity.entry_time),
        "exitTime": str(new_entity.exit_time),
        "imageTime": str(new_entity.image_time),
    }
    headers = {"authorization": "Token " + auth_token}
    response = requests.post(
        "{}/v1/motion".format(server_url), json=metadata, headers=headers
    )
    data = __parse_response(response, 201)
    image_id = data["id"]

    file_name = "{}.jpg".format(image_id)
    file_location = os.path.join(data_location, file_name)

    imwrite(file_location, new_entity.best_image)

    image_file = {"file": open(file_location, "rb")}
    response = requests.patch(
        "{}/v1/motion/{}".format(server_url, image_id), files=image_file
    )
    __parse_response(response, 202)


try:
    url = "http://localhost:8080"
    new_id, new_password = register_with_server(url)
    logger.info("[id: {}, password: {}]".format(new_id, new_password))
    token = get_access_token(url, new_id, new_password)
    image = cv2.imread("test.jpg")
    entity = Entity(50, 20, image)
    add_motion(url, token, entity)
except ConnectionError as e:
    logger.error(e)
