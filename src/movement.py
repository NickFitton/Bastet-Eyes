import cv2
import logging

logger = logging.getLogger(__name__)


def background_diff_mog_2(image, fg_bg):
    fg_mask = fg_bg.apply(image)
    threshold = cv2.threshold(fg_mask, 128, 255, cv2.THRESH_BINARY)[1]
    cv2.imshow("mog_threshold", fg_mask)
    return (
        cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[
            1
        ],
        fg_bg,
    )
