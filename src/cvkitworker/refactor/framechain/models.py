from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class FrameInfo:
    shm_name: str
    shape: Tuple[int, ...]
    dtype: str
    timestamp: Optional[float] = None


@dataclass
class Detection:
    name: str
    polygon: List[Tuple[int, int]]
    metadata: Optional[dict] = None