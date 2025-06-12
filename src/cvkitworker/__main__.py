import argparse
import os
import json
import tempfile
from cvkitworker.config.parse_config import ConfigParser
from cvkitworker.detectors.frame_worker import FrameWorker
from cvkitworker.detectors.detect_worker import DetectWorker
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, shared_memory
from loguru import logger

num_workers = 2  # Number of worker processes to spawn


def create_file_config(file_path):
    """Create temporary configuration for file input."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    
    config = {
        "receivers": [
            {
                "name": "file_input",
                "type": "file",
                "source": file_path
            }
        ],
        "detectors": [
            {
                "name": "face_detector",
                "type": "face_detector",
                "frequency_ms": 500,
                "scale": 1.0,
                "model_path": "mmod_human_face_detector.dat",
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640,
                "height": 480
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        return f.name


def create_webcam_config():
    """Create temporary configuration for webcam input."""
    config = {
        "receivers": [
            {
                "name": "webcam_input",
                "type": "webcam",
                "source": 0
            }
        ],
        "detectors": [
            {
                "name": "face_detector",
                "type": "face_detector",
                "frequency_ms": 500,
                "scale": 1.0,
                "model_path": "mmod_human_face_detector.dat",
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640,
                "height": 480
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        return f.name



def main():
    logger.info(f"Main process started. PID: {os.getpid()}")

    parser = argparse.ArgumentParser(description="cvkit.io worker")
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--file', type=str, help='Path to video file for testing')
    parser.add_argument('--webcam', action='store_true', help='Use webcam for testing')
    
    args = parser.parse_args()
    
    # Determine configuration source
    config_file = None
    if os.getenv("CVKIT_CONFIG") is not None:
        config_file = os.getenv("CVKIT_CONFIG")
    elif args.config:
        config_file = args.config
    elif args.file:
        # Create temporary config for file input
        config_file = create_file_config(args.file)
    elif args.webcam:
        # Create temporary config for webcam
        config_file = create_webcam_config()
    else:
        parser.error("Must specify --config, --file, or --webcam")

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
            logger.info(f"Spawning FrameWorker and {num_workers} "
                       f"DetectWorkers. PID: {os.getpid()}")
            producer = executor.submit(frame_worker.run)
            
            for i in range(num_workers):
                detect_worker = DetectWorker(work_queue, shm.name)
                # Start multiple detect workers
                consumers.append(executor.submit(detect_worker.run))
            # Wait for the result
            producer.result()
            for i in range(num_workers):
                consumers[i].result()
    logger.info("All workers finished. Cleaning up shared memory.")
    frame_worker.unload()
    for i in range(num_workers):
        consumers[i].unload()
    # Clean up shared memory
    shm.close()
    shm.unlink()  # Remove the shared memory block
    logger.info("Shutdown complete.")



if __name__ == "__main__":
    main()
