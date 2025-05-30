from detect.detectors.detector import Detector
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class FaceDetector(Detector):
    def __init__(self, detector_name: str):
        #super().__init__()
        self.detector_name = detector_name
        self.detector_lib = None
        self.load()

    def load(self):
        base_dir = Path(__file__).resolve().parent
        if self.detector_name == "dlib":
            import dlib
            self.detector_lib = dlib.get_frontal_face_detector()
            print(f"Loaded dlib face detector")
        elif self.detector_name == "dlib_cnn":
            import dlib
            self.detector_lib = dlib.cnn_face_detection_model_v1(
                os.path.join(base_dir, "models", "mmod_human_face_detector.dat")
        )
        else:
            raise ValueError(f"Unknown detector: {self.detector_name}")

    def detect(self, frame):
        start = time.time()
        print(f"Detecting faces using {self.detector_name} detector")
        match self.detector_name:
            case "dlib_cnn":
                faces = self.detector_lib(frame, 1)  # dlib cnn
                faces = [r.rect for r in faces]
            case "yunet":
                faces = self.detector_lib.detect(frame)
                #for face in faces:
                #    x, y, w, h = face[0], face[1], face[2], face[3]
            case "dlib":
                print("Using dlib frontal face detector")
                faces = self.detector_lib(frame, 0)
                #for i, face in enumerate(faces):
                #    x, y, w, h = face.left(), face.top(), face.width(), face.height()
        
        print(f"Face detection took {(time.time() - start) * 1000}ms")

        return faces
    

