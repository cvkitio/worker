from typing import Any, Tuple
import numpy as np
import time
import os
from ..base import Markuper


class FaceMarkup(Markuper):
    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        print(f"FaceMarkup {os.getpid()}")
        time.sleep(0.02)
        return frame, meta