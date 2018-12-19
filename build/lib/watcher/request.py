import uuid
import requests
import logging
from requests.exceptions import InvalidSchema

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())


def register_with_server(server_url):
    password = uuid.uuid4()
    body = {"password": "{}".format(password)}

    try:
        response = requests.post("{}/v1/camera".format(server_url), json=body).json()
        logger.info(response)
    except InvalidSchema:
        logger.error("Failed to connect to server")


register_with_server("localhost:8080")
