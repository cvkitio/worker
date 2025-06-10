class DetectorLoader:
    def __init__(self, detectors_config: str):
        self.model_path = detectors_config
        self.detectors = []

    def load_model(self):
        # Load the model from the specified path
        for detector in self.detectors_config:
            if detector["type"] == "face_detector":
                # Load face detection model
                from detectors.face_detect import FaceDetector
                self.model = FaceDetector(
                    model_path=detector["model_path"],
                    device=detector["device"])
            else:
                raise ValueError(f"Unknown detector type: "
                                 f"{detector['type']}")
