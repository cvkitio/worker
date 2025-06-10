"""Main entry point for CVKit.io Worker."""

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, shared_memory

from loguru import logger

from .config import ConfigParser
from .detectors.detect_worker import DetectWorker
from .detectors.frame_worker import FrameWorker


def create_webcam_config():
    """Create a default configuration for webcam mode."""
    webcam_config = {
        "receivers": [
            {
                "name": "webcam",
                "type": "webcam",
                "device_id": 0
            }
        ],
        "preprocessors": [
            {
                "name": "resize",
                "type": "resize",
                "width": 640,
                "height": 480
            }
        ],
        "detectors": [
            {
                "name": "face_detector",
                "type": "dlib_cnn",
                "frequency_ms": 500.0
            }
        ],
        "actions": []
    }
    
    # Create a simple config object that behaves like ConfigParser
    class SimpleConfig:
        def __init__(self, config_dict):
            self.config = config_dict
            
        def get_config(self):
            return self.config
            
        def get(self, key, default=None):
            return self.config.get(key, default)
    
    logger.info("Created default webcam configuration:")
    logger.info("  - Webcam input (device 0)")
    logger.info("  - Face detection enabled")
    logger.info("  - 640x480 processing resolution")
    
    return SimpleConfig(webcam_config)


def main():
    """Main entry point."""
    logger.info(f"Main process started. PID: {os.getpid()}")

    parser = argparse.ArgumentParser(description="cvkit.io worker")
    parser.add_argument('--config', type=str,
                       help='Path to config file')
    parser.add_argument('--webcam', action='store_true',
                       help='Use webcam instead of config file (quick test mode)')
    
    args = parser.parse_args()
    
    # Determine config file
    if args.webcam:
        # Use webcam mode - create a temporary config
        config_file = None
        logger.info("Using webcam mode - creating temporary configuration")
    elif args.config:
        config_file = args.config
    elif os.getenv("CVKIT_CONFIG") is not None:
        config_file = os.getenv("CVKIT_CONFIG")
    else:
        parser.error("Must specify either --config <file> or --webcam")

    # Create config parser
    if args.webcam:
        # Create a default webcam configuration
        config_parser = create_webcam_config()
    else:
        config_parser = ConfigParser(config_file)

    with Manager() as manager:
        # Shared memory can be used to share data between processes
        # TODO this is currently for one frame, we should make it the
        # same size as the target frame
        shm = shared_memory.SharedMemory(create=True,
                                        size=1024 * 1024 * 1024)
        logger.info(f"Shared memory created with name {shm.name} and "
                   f"size {shm.size}")

        work_queue = manager.Queue()
        # TODO use multiprocessing.shared_memory to share the queue
        # between processes
        frame_worker = FrameWorker(config_parser.get_config(),
                                  work_queue, shm.name)

        consumers = []
        with ProcessPoolExecutor() as executor:
            logger.info(f"Spawning FrameWorker and {2} "
                       f"DetectWorkers. PID: {os.getpid()}")
            producer = executor.submit(frame_worker.run)

            for i in range(2):
                detect_worker = DetectWorker(work_queue, shm.name)
                # Start multiple detect workers
                consumers.append(executor.submit(detect_worker.run))
            # Wait for the result
            producer.result()
            for i in range(2):
                consumers[i].result()
    logger.info("All workers finished. Cleaning up shared memory.")
    frame_worker.unload()
    for i in range(2):
        consumers[i].unload()
    # Clean up shared memory
    shm.close()
    shm.unlink()  # Remove the shared memory block
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()