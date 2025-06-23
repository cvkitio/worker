from typing import Any, Tuple
import numpy as np
import time
import os
from ..base import Outputer


class OutputFile(Outputer):
    def __init__(self, filename: str):
        self.filename = filename

    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        print(f"Saving frame to {self.filename} {os.getpid()}")
        time.sleep(0.1)
        return frame, meta