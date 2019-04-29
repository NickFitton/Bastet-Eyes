from threading import Thread
from requests import post, patch
from os.path import join, isdir
from os import remove, mkdir
from cv2 import imwrite
from time import sleep
import logging


class Reporter(Thread):
    # Initialization of the reporter thread, loads with everything it needs to communicate with the server
    def __init__(
        self, queue, terminate_event, host, auth_token, tmp_location="/tmp/watcher"
    ):
        self.host = host
        self.queue = queue
        self.term_event = terminate_event
        self.headers = {"authorization": "Token {}".format(auth_token)}
        self.storage_location = tmp_location
        if not isdir(tmp_location):
            mkdir(tmp_location)
        self.logger = logging.getLogger(__name__)
        Thread.__init__(self, name="Reporter", daemon=True)

    # Posts a new entity to the backend
    def post_new_motion(self, _entity):
        self.logger.info("Posting new motion")
        metadata = {
            "entryTime": str(_entity.first_active),
            "exitTime": str(_entity.last_active),
            "imageTime": str(_entity.image_time),
        }
        response = post(
            "{}/v1/motion".format(self.host), json=metadata, headers=self.headers
        )
        if response.status_code == 201:
            return response.json()["data"]["id"]
        else:
            raise ConnectionError(
                "Bad communication with server[status={}, error={}]".format(
                    response.status_code, response.json()["error"]
                )
            )

    # Updates a given entity with an image
    def patch_motion(self, _entity, _id):
        self.logger.info("Patching motion {} with image".format(_id))
        file_name = "{}.jpg".format(_id)
        file_location = join(self.storage_location, file_name)

        imwrite(file_location, _entity.best_image)

        image_file = {"file": open(file_location, "rb")}
        response = patch(
            "{}/v1/motion/{}".format(self.host, _id),
            files=image_file,
            headers=self.headers,
        )
        if response.status_code == 202:
            remove(file_location)
        else:
            raise ConnectionError(
                "Bad communication with server[status={}, error={}]".format(
                    response.status_code, response.json()["error"]
                )
            )

    def run(self):
        while not self.term_event.is_set():
            while not self.queue.empty():
                self.logger.info("Entity received")
                entity = self.queue.get()

                entity_id = self.post_new_motion(entity)
                self.patch_motion(entity, entity_id)
                self.queue.task_done()
                self.logger.info("Entity processed")
            sleep(1)
