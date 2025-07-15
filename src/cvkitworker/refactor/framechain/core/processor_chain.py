from typing import List
import numpy as np
from ..base import Processor


class ProcessorChain:
    def __init__(self, processors: List[Processor]):
        self.processors = processors

    def run(self, frame: np.ndarray):
        meta = None
        for processor in self.processors:
            frame, meta = processor.process(frame, meta)
        return frame