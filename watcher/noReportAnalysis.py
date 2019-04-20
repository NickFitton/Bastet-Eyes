from threading import Event
from queue import Queue
from watcher.streamReader import StreamReader, FrameProcessor, ContourFinder
from time import time
from cv2 import rectangle, imshow, waitKey, destroyAllWindows
import logging

logging.basicConfig(
    format="[%(threadName)s\t] %(asctime)s - %(levelname)s:\t%(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

min_contour_area = 100
media_url = "http://195.1.188.76/mjpg/video.mjpg"
# media_url = "http://166.247.77.253:81/mjpg/video.mjpg"
scale = 0.5

terminate_event = Event()
frame_queue = Queue()
processed_frame_queue = Queue()
contour_frame_queue = Queue()

last_fps_print = time()
printerval = 5

threads = []
threads.append(StreamReader(frame_queue, terminate_event, media_url))
threads.append(
    FrameProcessor(frame_queue, processed_frame_queue, terminate_event, scale)
)
threads.append(
    ContourFinder(
        processed_frame_queue, contour_frame_queue, terminate_event, 0, min_contour_area
    )
)

for thread in threads:
    thread.start()

frame_count = 0

logger.info("FPS\tA\tB\tC")
while not terminate_event.is_set():
    if not contour_frame_queue.empty():
        entities, colored_frame = contour_frame_queue.get()

        for entity in entities:
            if entity.size() > 50:
                if entity.alive:
                    rectangle(
                        colored_frame,
                        entity.scaled_p1(scale),
                        entity.scaled_p2(scale),
                        (0, 255, 0),
                    )
                else:
                    rectangle(
                        colored_frame,
                        entity.scaled_p1(scale),
                        entity.scaled_p2(scale),
                        (0, 0, 255),
                    )
        frame_count += 1
        imshow("Stream", colored_frame)
        contour_frame_queue.task_done()
    key = waitKey(1)
    if key == ord("q"):
        terminate_event.set()

    if (time() - last_fps_print) > printerval:
        logger.info(
            "{},\t{},\t{},\t{}".format(
                int(frame_count / printerval),
                frame_queue.qsize(),
                processed_frame_queue.qsize(),
                contour_frame_queue.qsize(),
            )
        )
        if frame_count == 0:
            logger.warn(
                "No frames in last {} seconds, stream has died".format(printerval)
            )
            terminate_event.set()
        last_fps_print = time()
        frame_count = 0

destroyAllWindows()
