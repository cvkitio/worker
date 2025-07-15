from abc import ABC, abstractmethod
from typing import Any, Tuple
import numpy as np


class Processor(ABC):
    @abstractmethod
    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        pass


class PreProcessor(Processor):
    pass


class Detector(Processor):
    pass


class Markuper(Processor):
    pass


class Outputer(Processor):
    pass