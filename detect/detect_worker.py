from multiprocessing import shared_memory
import time
import os

import cv2
import numpy as np
from detect.detectors.detector import Detector
from detect.detectors.face_detect import FaceDetector
from detect.frame import Frame

class DetectWorker:
    def __init__(self, queue, shared_memory_name):
        self.queue = queue
        self.shared_memory_name = shared_memory_name
        self.face_detector = None
        self.load()
        
    def load(self):
        # Load any necessary configuration for the detection worker
        print("Loading configuration for DetectWorker...")
        # This could include loading models, setting up logging, etc.
        # This needs to dynamically load the various detectors based on the configuration
        self.face_detector = FaceDetector("dlib")
        pass

    def run(self):
        print(f"DetectWorker started, waiting for items in the queue... pid: {os.getpid()}")
        while True:
            if not self.queue.empty():
                frame_data: Frame = self.queue.get()
                
                print(f"{os.getpid()} Processing item from queue: {frame_data.detector} ")
                # Get the frame from shared memory
                shm = shared_memory.SharedMemory(name=self.shared_memory_name)
                frame = np.ndarray(frame_data.shape, dtype=frame_data.frame_type, buffer=shm.buf)
                print(f"Frame shape: {frame.shape}, type: {frame.dtype}")
                # Convert the frame to Grayscale if needed
                #if frame_data.frame_type == "uint8":
                #    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Use opencv to show the frame
                cv2.imshow(f"{os.getpid()} Frame", frame)     
                #cv2.waitKey(1)          
                match frame_data.detector:
                    case "face_detector":
                        faces = self.face_detector.detect(frame)  # Replace None with the actual frame
                        print(f"Detected faces: {len(faces)}")
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                time.sleep(0.1)