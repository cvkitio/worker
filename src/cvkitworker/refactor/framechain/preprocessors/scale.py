from typing import Any, Tuple
import numpy as np
import time
import os
from ..base import PreProcessor


class Scale(PreProcessor):
    def __init__(self, scale_factor: float):
        self.scale_factor = scale_factor

    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        print(f"Scale {os.getpid()}")
        time.sleep(0.01)
        return frame, meta