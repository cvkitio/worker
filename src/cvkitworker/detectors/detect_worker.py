from multiprocessing import shared_memory
import time
import os
import signal

import cv2
import numpy as np
from .detectors.face_detect import FaceDetector
from .frame import Frame
from loguru import logger


class DetectWorker:
    def __init__(self, queue, shared_memory_name):
        self.queue = queue
        self.shared_memory_name = shared_memory_name
        self.face_detector = None
        self.shutdown_requested = False
        
        # Register signal handler for this worker
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals in worker process."""
        logger.info(f"DetectWorker received signal {signum}. Requesting shutdown...")
        self.shutdown_requested = True

    def load(self):
        # Load any necessary configuration for the detection worker
        # This could include loading models, setting up logging, etc.
        # This needs to dynamically load the various detectors based on
        # the configuration
        self.face_detector = FaceDetector("dlib")  # Use basic dlib detector as default
        logger.info(f"Loaded configuration for DetectWorker. PID: "
                    f"{os.getpid()}")

    def run(self):
        self.load()
        logger.info(f"DetectWorker started, waiting for items in the "
                    f"queue... PID: {os.getpid()}")
        
        while not self.shutdown_requested:
            try:
                if not self.queue.empty():
                    frame_data = self.queue.get()
                    
                    # Check if it's a stop signal
                    if frame_data == "STOP":
                        logger.info(f"DetectWorker PID {os.getpid()} received STOP signal")
                        break
                        
                    if isinstance(frame_data, Frame):
                        logger.info(f"{os.getpid()} Processing item from queue: "
                                    f"{frame_data.detector}")
                        # Get the frame from shared memory
                        shm = shared_memory.SharedMemory(name=self.shared_memory_name)
                        frame = np.ndarray(frame_data.shape,
                                           dtype=frame_data.frame_type,
                                           buffer=shm.buf)
                        logger.info(f"Frame shape: {frame.shape}, type: {frame.dtype}")
                        # Convert the frame to Grayscale if needed
                        # if frame_data.frame_type == "uint8":
                        #    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        # Use opencv to show the frame
                        cv2.imshow(f"{os.getpid()} Frame", frame)
                        # cv2.waitKey(1)
                        match frame_data.detector:
                            case "face_detector":
                                faces = self.face_detector.detect(frame)
                                # Replace None with the actual frame
                                logger.info(f"Detected faces: {len(faces)}. PID: "
                                            f"{os.getpid()}")
                        
                        # Check for shutdown after processing
                        if self.shutdown_requested:
                            break
                            
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        logger.info(f"DetectWorker PID {os.getpid()} received "
                                    f"'q' key press.")
                        break
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in DetectWorker: {e}")
                if self.shutdown_requested:
                    break
                    
        logger.info(f"DetectWorker PID {os.getpid()} exiting")
        self.unload()
    
    def unload(self):
        """Clean up resources."""
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            logger.warning(f"Error closing OpenCV windows: {e}")
