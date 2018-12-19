import requests
import logging
import random
import string
import os
from requests.exceptions import InvalidSchema

logging.basicConfig(
    format="%(asctime)s - %(levelname)s:\t%(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
credentials_location = "/tmp/watcher"
credentials_file_name = "credentials.csv"


def generate_password():
    return "".join(
        random.SystemRandom().choice(string.ascii_letters + string.digits)
        for _ in range(20)
    )


def save_credentials(camera_id, password):
    if not os.path.isdir(credentials_location):
        os.mkdir(credentials_location)
    with open(os.path.join(credentials_location, credentials_file_name), "w+") as file:
        file.write("{},{}".format(camera_id, password))


def load_credentials():
    with open(os.path.join(credentials_location, credentials_file_name), "r") as file:
        return file.read().split(",")


def credentials_exist():
    return os.path.isfile(os.path.join(credentials_location, credentials_file_name))


def register_with_server(server_url):
    if credentials_exist():
        logger.debug("Loading previously saved credentials")
        return load_credentials()

    password = generate_password()
    body = {"password": password}

    try:
        response = requests.post("{}/v1/cameras".format(server_url), json=body)
        json = response.json()
        if not response.status_code == 201:
            logger.error(
                "Server returned bad request with status {}".format(
                    response.status_code
                )
            )
            if "error" in json:
                raise ConnectionError(
                    "Bad communication with server[status={}, error={}}".format(
                        response.status_code, json["error"]
                    )
                )
            else:
                raise ConnectionError(
                    "Bad communication with server[status={}]".format(
                        response.status_code
                    )
                )
        if "error" in json:
            raise ConnectionError(
                "Bad communication with server[status={}, error={}]".format(
                    response.status_code, json["error"]
                )
            )
        elif "data" in json:
            data = json["data"]
            save_credentials(data["id"], password)
            return data["id"], password
        else:
            raise ConnectionError(
                "Bad communication with server[status={}, body={}]".format(
                    response.status_code, json
                )
            )
    except InvalidSchema:
        raise ConnectionError("Failed to connect to server")


try:
    new_id, new_password = register_with_server("http://localhost:8080")
    logger.info("[id: {}, password: {}]".format(new_id, new_password))
except ConnectionError as e:
    logger.error(e)
