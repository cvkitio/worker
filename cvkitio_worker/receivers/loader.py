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
            elif config["type"] == "webcam":
                # Load webcam receiver
                device_id = config.get("device_id", 0)  # Default to device 0
                logger.info(f"Loading webcam device {device_id}")
                self.video_capture = cv2.VideoCapture(device_id)
                
                # Check if webcam opened successfully
                if not self.video_capture.isOpened():
                    logger.error(f"Failed to open webcam device {device_id}")
                    raise ValueError(f"Could not open webcam device {device_id}")
                else:
                    # Test reading a frame to verify webcam is working
                    ret, test_frame = self.video_capture.read()
                    if ret:
                        logger.info(f"Webcam device {device_id} successfully opened and tested")
                        logger.info(f"Webcam resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    else:
                        logger.error(f"Webcam device {device_id} opened but cannot read frames")
                        self.video_capture.release()
                        raise ValueError(f"Webcam device {device_id} cannot read frames")
            elif config["type"] == "http":
                # Load HTTP receiver
                # self.load_http_receiver(config)
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
