from dataclasses import dataclass
from detect.detectors.detector import Detector
from typing import Any

@dataclass
class Frame:
    frame_id: str
    shape: tuple
    frame_type: str
    detector: str
    timestamp: int
    shared_memory_name: str
    #shared_memory_lock: Any # Lock for accessing shared memory

    def __repr__(self):
        return f"Frame(frame_id={self.frame_id}, frame={self.frame})"