from detect.detectors.detector import Detector

class Frame:
    def __init__(self, frame_id: int, frame: str, timestamp: float, detectors: list[Detector]):
        self.frame_id = frame_id
        self.frame = frame
        self.timestamp = timestamp
        self.detectors = detectors

    def __repr__(self):
        return f"Frame(frame_id={self.frame_id}, frame={self.frame})"