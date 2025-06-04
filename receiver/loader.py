import cv2
from loguru import logger
import os


class ReceiverLoader:
    def __init__(self, receivers):
        self.receivers = receivers
        self.video_capture = None
        self.load()

    def load(self):
        logger.info(f"Receiver config: {self.receivers} (PID: {os.getpid()})")
        # Load the receiver configuration
        for config in self.receivers:
            if config["type"] == "rtsp":
                # Load RTSP receiver
                self.video_capture = cv2.VideoCapture(config["url"])
            elif config["type"] == "http":
                # Load HTTP receiver
                #self.load_http_receiver(config)
                pass
            else:
                raise ValueError(f"Unknown receiver type: {config['type']}")
            # we will only deal with one receiver for now
            break
        pass
    
    def get_video_capture(self):
        # Return the video capture object
        if self.video_capture is None:
            raise ValueError("Receiver not loaded")
        return self.video_capture

    def unload(self):
        # Unload the receiver configuration
        pass