from multiprocessing import shared_memory
import cv2
import time
import os
import signal
import numpy as np
from loguru import logger

from .loader import DetectorLoader
from cvkitworker.receivers.loader import ReceiverLoader
from .frame import Frame
from ..utils.timing import (
    measure_frame_processing,
    measure_scaling,
    measure_color_conversion
)


class FrameWorker:
    def __init__(self, config, queue, shared_memory_name):
        self.receiver_config = config["receivers"]
        self.detectors = config["detectors"]
        self.preprocessors = config["preprocessors"]
        self.shared_memory_name = shared_memory_name
        self.video_capture = None
        self.receiver = None
        self.queue = queue
        self.shutdown_requested = False
        
        # Register signal handler for this worker
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals in worker process."""
        logger.info(f"FrameWorker received signal {signum}. Requesting shutdown...")
        self.shutdown_requested = True

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

    @measure_frame_processing
    def preprocess_frame(self, frame):
        # Apply any preprocessing steps defined in the configuration
        for preprocessor in self.preprocessors:
            match preprocessor["type"]:
                case "resize":
                    width = preprocessor.get("width")
                    height = preprocessor.get("height")
                    # Convert to int if provided, otherwise keep as None
                    width = int(width) if width is not None else None
                    height = int(height) if height is not None else None
                    frame = self._resize_frame(frame, width, height)
                case "grayscale":
                    frame = self._convert_to_grayscale(frame)
            # Add more preprocessing steps as needed
        return frame
    
    @measure_scaling
    def _resize_frame(self, frame, width, height):
        """Resize frame with timing measurement, maintaining aspect ratio.
        
        If only width is provided (height=None), scale to that width.
        If only height is provided (width=None), scale to that height.
        If both are provided, use the old behavior (may distort image).
        """
        orig_height, orig_width = frame.shape[:2]
        
        if width is not None and height is None:
            # Scale by width, maintain aspect ratio
            scale_factor = width / orig_width
            new_height = int(orig_height * scale_factor)
            return cv2.resize(frame, (width, new_height))
        elif height is not None and width is None:
            # Scale by height, maintain aspect ratio
            scale_factor = height / orig_height
            new_width = int(orig_width * scale_factor)
            return cv2.resize(frame, (new_width, height))
        else:
            # Both provided or both None - use original behavior
            if width is None and height is None:
                return frame
            return cv2.resize(frame, (width, height))
    
    @measure_color_conversion
    def _convert_to_grayscale(self, frame):
        """Convert frame to grayscale with timing measurement."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

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
        while self.video_capture.isOpened() and not self.shutdown_requested:
            ret, frame = self.video_capture.read()
            if not ret:
                logger.error(
                    f"Failed to retrieve frame (PID: {os.getpid()})"
                )
                # TODO: add retry logic and then exit
                break
            
            # Check for shutdown request
            if self.shutdown_requested:
                logger.info("Shutdown requested, stopping frame processing")
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

            # Check for 'q' key press or shutdown request
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or self.shutdown_requested:
                if key == ord('q'):
                    logger.info("'q' key pressed, stopping frame processing")
                break

        logger.info("FrameWorker exiting main loop")
        self.unload()

    def unload(self):
        # Unload the receiver configuration
        self.queue.put("STOP")
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()
