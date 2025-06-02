from detect.detectors.detector import Detector
import logging
import os
import time
from pathlib import Path
from loguru import logger

logger = logging.getLogger(__name__)

class FaceDetector(Detector):
    def __init__(self, detector_name: str):
        self.detector_name = detector_name
        self.detector_lib = None
        self.load()

    def load(self):
        base_dir = Path(__file__).resolve().parent
        if self.detector_name == "dlib":
            import dlib
            self.detector_lib = dlib.get_frontal_face_detector()
            logger.info(f"Loaded dlib face detector. PID: {os.getpid()}")
        elif self.detector_name == "dlib_cnn":
            import dlib
            self.detector_lib = dlib.cnn_face_detection_model_v1("/Users/andrewsinclair/.cache/kagglehub/datasets/leeast/mmod-human-face-detector-dat/versions/1/mmod_human_face_detector.dat")
            img = dlib.load_rgb_image("/Users/andrewsinclair/Desktop/id.png")
            dets = self.detector_lib(img, 1)
            logger.info(f"Loaded dlib_cnn face detector {len(dets)} faces detected. PID: {os.getpid()}")
        else:
            logger.error(f"Unknown detector: {self.detector_name}. PID: {os.getpid()}")
            raise ValueError(f"Unknown detector: {self.detector_name}")

    def detect(self, frame):
        start = time.time()
        logger.info(f"Detecting faces using {self.detector_name} detector. PID: {os.getpid()}")
        match self.detector_name:
            case "dlib_cnn":
                logger.info("Using dlib_cnn face detector")
                faces = self.detector_lib(frame, 0)
            case "yunet":
                faces = self.detector_lib.detect(frame)
            case "dlib":
                logger.info("Using dlib frontal face detector")
                faces = self.detector_lib(frame, 0)
        logger.info(f"Face detection took {(time.time() - start) * 1000}ms. PID: {os.getpid()}")
        return faces


