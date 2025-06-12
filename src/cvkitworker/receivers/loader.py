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
            elif config["type"] == "file":
                # Load file receiver
                file_path = config["source"]
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Video file not found: {file_path}")
                self.video_capture = cv2.VideoCapture(file_path)
                logger.info(f"Loaded video file: {file_path}")
            elif config["type"] == "webcam":
                # Load webcam receiver
                camera_index = config.get("source", 0)
                self.video_capture = cv2.VideoCapture(camera_index)
                logger.info(f"Loaded webcam with index: {camera_index}")
            elif config["type"] == "http":
                # Load HTTP receiver
                # self.load_http_receiver(config)
                pass
            else:
                raise ValueError(f"Unknown receiver type: {config['type']}")
            # we will only deal with one receiver for now
            break

    def get_video_capture(self):
        # Return the video capture object
        if self.video_capture is None:
            raise ValueError("Receiver not loaded")
        return self.video_capture

    def unload(self):
        # Unload the receiver configuration
        pass
