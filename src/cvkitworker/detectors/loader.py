class DetectorLoader:
    def __init__(self, detectors_config):
        self.detectors_config = detectors_config
        self.detectors = []

    def load_model(self):
        # Load the model from the specified path
        for detector in self.detectors_config:
            if detector["type"] == "face_detector":
                # Load face detection model
                from .detectors.face_detect import FaceDetector
                
                # Get detector variant (dlib, dlib_cnn, opencv_dnn, yunet)
                detector_name = detector.get("variant", "dlib")
                model_path = detector.get("model_path")
                device = detector.get("device", "cpu")
                
                self.model = FaceDetector(
                    detector_name=detector_name,
                    model_path=model_path,
                    device=device
                )
            else:
                raise ValueError(f"Unknown detector type: {detector['type']}")
