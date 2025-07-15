from typing import Optional, Tuple
import numpy as np
import time
import os
from ..base import Detector
from ..models import Detection


class FaceDetector(Detector):
    def process(self, frame: np.ndarray, meta=None) -> Tuple[np.ndarray, Optional[Detection]]:
        print(f"FaceDetect {os.getpid()}")
        time.sleep(0.2)
        return frame, Detection("face", [(10, 10), (100, 100)])