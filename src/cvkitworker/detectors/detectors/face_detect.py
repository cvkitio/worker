from .detector import Detector
import os
import time
import cv2
import numpy as np
from pathlib import Path
from loguru import logger


class FaceDetector(Detector):
    def __init__(self, detector_name: str, model_path: str = None, device: str = "cpu"):
        self.detector_name = detector_name
        self.model_path = model_path
        self.device = device
        self.detector_lib = None
        self.models_dir = Path("models")
        self.load()

    def _find_model_file(self, filename: str):
        """Find model file in models directory or download if needed."""
        model_file = self.models_dir / filename
        
        if not model_file.exists():
            logger.warning(f"Model file not found: {model_file}")
            logger.info("Attempting to download models...")
            
            # Try to run download script
            try:
                import subprocess
                import sys
                script_path = Path("scripts/download_models.py")
                if script_path.exists():
                    subprocess.run([sys.executable, str(script_path)], check=True)
                    
                    # Check if file exists now
                    if model_file.exists():
                        logger.info(f"Successfully downloaded: {model_file}")
                        return str(model_file)
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to download models: {e}")
            
            # File still doesn't exist
            raise FileNotFoundError(f"Model file not found: {model_file}. "
                                    f"Run 'python scripts/download_models.py' to download required models.")
        
        return str(model_file)

    def load(self):
        logger.info(f"Loading {self.detector_name} face detector on {self.device}. PID: {os.getpid()}")
        
        if self.detector_name == "dlib":
            import dlib
            self.detector_lib = dlib.get_frontal_face_detector()
            logger.info(f"Loaded dlib frontal face detector. PID: {os.getpid()}")
            
        elif self.detector_name == "dlib_cnn":
            import dlib
            
            # Use provided model path or find default
            if self.model_path and os.path.exists(self.model_path):
                model_file = self.model_path
            else:
                model_file = self._find_model_file("mmod_human_face_detector.dat")
            
            self.detector_lib = dlib.cnn_face_detection_model_v1(model_file)
            logger.info(f"Loaded dlib CNN face detector from {model_file}. PID: {os.getpid()}")
            
        elif self.detector_name == "opencv_dnn":
            # Use provided model path or find default
            if self.model_path and os.path.exists(self.model_path):
                model_file = self.model_path
                config_file = self.model_path.replace('.pb', '.pbtxt')
            else:
                model_file = self._find_model_file("opencv_face_detector_uint8.pb")
                config_file = self._find_model_file("opencv_face_detector.pbtxt")
            
            self.detector_lib = cv2.dnn.readNetFromTensorflow(model_file, config_file)
            logger.info(f"Loaded OpenCV DNN face detector from {model_file}. PID: {os.getpid()}")
            
        elif self.detector_name == "yunet":
            # Use provided model path or find default
            if self.model_path and os.path.exists(self.model_path):
                model_file = self.model_path
            else:
                model_file = self._find_model_file("face_detection_yunet_2023mar.onnx")
            
            self.detector_lib = cv2.FaceDetectorYN.create(
                model=model_file,
                config="",
                input_size=(640, 480),
                score_threshold=0.6,
                nms_threshold=0.3,
                top_k=5000
            )
            logger.info(f"Loaded YuNet face detector from {model_file}. PID: {os.getpid()}")
            
        else:
            logger.error(f"Unknown detector: {self.detector_name}. PID: {os.getpid()}")
            raise ValueError(f"Unknown detector: {self.detector_name}. "
                           f"Supported: dlib, dlib_cnn, opencv_dnn, yunet")

    def detect(self, frame):
        """Detect faces in frame and return consistent format."""
        start = time.time()
        logger.debug(f"Detecting faces using {self.detector_name} detector. PID: {os.getpid()}")
        
        faces = []
        
        try:
            if self.detector_name == "dlib":
                # Convert BGR to RGB for dlib
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detections = self.detector_lib(rgb_frame, 0)
                
                for detection in detections:
                    faces.append({
                        'x': detection.left(),
                        'y': detection.top(),
                        'width': detection.width(),
                        'height': detection.height(),
                        'confidence': 1.0  # dlib doesn't provide confidence
                    })
                    
            elif self.detector_name == "dlib_cnn":
                # Convert BGR to RGB for dlib
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                detections = self.detector_lib(rgb_frame, 0)
                
                for detection in detections:
                    rect = detection.rect
                    faces.append({
                        'x': rect.left(),
                        'y': rect.top(),
                        'width': rect.width(),
                        'height': rect.height(),
                        'confidence': detection.confidence
                    })
                    
            elif self.detector_name == "opencv_dnn":
                height, width = frame.shape[:2]
                
                # Create blob from frame
                blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123])
                self.detector_lib.setInput(blob)
                detections = self.detector_lib.forward()
                
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > 0.5:  # Confidence threshold
                        x1 = int(detections[0, 0, i, 3] * width)
                        y1 = int(detections[0, 0, i, 4] * height)
                        x2 = int(detections[0, 0, i, 5] * width)
                        y2 = int(detections[0, 0, i, 6] * height)
                        
                        faces.append({
                            'x': x1,
                            'y': y1,
                            'width': x2 - x1,
                            'height': y2 - y1,
                            'confidence': float(confidence)
                        })
                        
            elif self.detector_name == "yunet":
                height, width = frame.shape[:2]
                self.detector_lib.setInputSize((width, height))
                
                _, detections = self.detector_lib.detect(frame)
                
                if detections is not None:
                    for detection in detections:
                        x, y, w, h = detection[:4].astype(int)
                        confidence = detection[14]
                        
                        faces.append({
                            'x': x,
                            'y': y,
                            'width': w,
                            'height': h,
                            'confidence': float(confidence)
                        })
                        
        except Exception as e:
            logger.error(f"Error during face detection: {e}")
            
        elapsed_ms = (time.time() - start) * 1000
        logger.info(f"Face detection took {elapsed_ms:.1f}ms, found {len(faces)} faces. PID: {os.getpid()}")
        
        return faces
