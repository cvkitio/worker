from multiprocessing import shared_memory
import cv2
import time
import os
import numpy as np
from loguru import logger

from detect.loader import DetectorLoader
from receiver.loader import ReceiverLoader
from detect.frame import Frame


class FrameWorker:
    def __init__(self, config, queue, shared_memory_name):
        self.receiver_config = config["receivers"]
        self.detectors = config["detectors"]
        self.preprocessors = config["preprocessors"]
        self.shared_memory_name = shared_memory_name
        self.video_capture = None
        self.receiver = None
        self.queue = queue

    def load(self):
        # Load the receiver configuration
        self.receiver = ReceiverLoader(self.receiver_config)
        self.video_capture = self.receiver.get_video_capture()
        if not self.video_capture.isOpened():
            raise ValueError("Failed to open video capture")

    def get_root_detectors(self):
        detectors = []
        for detector in self.detectors:
            if "parent" not in detector or detector["parent"] is None:
                detectors.append(detector)
        return detectors

    def preprocess_frame(self, frame):
        # Apply any preprocessing steps defined in the configuration
        for preprocessor in self.preprocessors:
            match preprocessor["type"]:
                case "resize":
                    width = int(preprocessor.get("width", frame.shape[1]))
                    height = int(preprocessor.get("height", frame.shape[0]))
                    frame = cv2.resize(frame, (width, height))
                case "grayscale":
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Add more preprocessing steps as needed
        return frame

    def run(self):
        logger.info(
            f"FrameWorker started pid: {os.getpid()}"
        )
        self.load()
        # Ideally what we want to do is have each type of detector
        # already loaded and then we can just call detector.detect(frame)
        detectors = self.get_root_detectors()
        DetectorLoader(detectors)

        last_processed_time = time.time()
        while self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if not ret:
                logger.error(
                    f"Failed to retrieve frame (PID: {os.getpid()})"
                )
                # TODO: add retry logic and then exit
                break
            frame = self.preprocess_frame(frame)

            elapsed_time = (
                (time.time() - last_processed_time) * 1000
            )  # Convert to milliseconds
            for detector in detectors:
                if elapsed_time > float(detector["frequency_ms"]):
                    # Scale the frame to the desired size
                    if "scale" in detector:
                        scale = float(detector["scale"])
                        frame = cv2.resize(
                            frame, (0, 0), fx=scale, fy=scale
                        )

                    # Copy frame to shared memory
                    logger.info(
                        f"Worker: Frame shape: {frame.shape}, "
                        f"type: {frame.dtype} (PID: {os.getpid()})"
                    )
                    shm = shared_memory.SharedMemory(
                        name=self.shared_memory_name
                    )
                    shm_array = np.ndarray(
                        frame.shape, dtype=frame.dtype, buffer=shm.buf
                    )
                    np.copyto(shm_array, frame)

                    # Create a Frame object to send to the queue
                    frame_data = Frame(
                        detector=detector['name'],
                        frame_id=str(time.time()),
                        shape=frame.shape,
                        frame_type=frame.dtype,
                        timestamp=int(time.time() * 1000),
                        shared_memory_name=self.shared_memory_name,
                        # shared_memory_lock=Lock()
                    )

                    last_processed_time = time.time()
                    self.queue.put(frame_data)
                    logger.info(
                        f"Sent to queue: {detector['name']} "
                        f"(PID: {os.getpid()})"
                    )

            # Process the frame (e.g., run detection)
            # For now, we will just display the frame
            # cv2.imshow('RTSP Stream', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.unload()

    def unload(self):
        # Unload the receiver configuration
        self.queue.put("STOP")
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()
