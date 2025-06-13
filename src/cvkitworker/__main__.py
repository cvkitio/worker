import argparse
import os
import json
import tempfile
import signal
import sys
import atexit
from cvkitworker.config.parse_config import ConfigParser
from cvkitworker.detectors.frame_worker import FrameWorker
from cvkitworker.detectors.detect_worker import DetectWorker
from concurrent.futures import ProcessPoolExecutor, TimeoutError
from multiprocessing import Manager, shared_memory
from loguru import logger


# Global variables for graceful shutdown
shutdown_requested = False
cleanup_done = False
executor = None
frame_worker = None
consumers = []
shm = None


def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) and SIGTERM gracefully."""
    global shutdown_requested
    
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name} signal. Initiating graceful shutdown...")
    shutdown_requested = True
    
    # Try to gracefully shutdown
    cleanup_and_exit(0)


def cleanup_and_exit(exit_code=0):
    """Clean up resources and exit."""
    global executor, frame_worker, consumers, shm, cleanup_done
    
    if cleanup_done:
        return  # Avoid double cleanup
    
    cleanup_done = True
    logger.info("Starting cleanup process...")
    
    try:
        # Shutdown the ProcessPoolExecutor
        if executor is not None:
            logger.info("Shutting down process executor...")
            executor.shutdown(wait=False)
            
        # Unload frame worker
        if frame_worker is not None:
            logger.info("Unloading frame worker...")
            try:
                frame_worker.unload()
            except Exception as e:
                logger.warning(f"Error unloading frame worker: {e}")
        
        # Unload consumers
        logger.info(f"Unloading {len(consumers)} detect workers...")
        for i, consumer in enumerate(consumers):
            try:
                if hasattr(consumer, 'unload'):
                    consumer.unload()
            except Exception as e:
                logger.warning(f"Error unloading consumer {i}: {e}")
        
        # Clean up shared memory
        if shm is not None:
            logger.info("Cleaning up shared memory...")
            try:
                shm.close()
                shm.unlink()
            except Exception as e:
                logger.warning(f"Error cleaning up shared memory: {e}")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    logger.info("Cleanup complete. Exiting.")
    sys.exit(exit_code)


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
                "variant": "dlib",
                "frequency_ms": 500,
                "scale": 1.0,
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640
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
                "variant": "dlib",
                "frequency_ms": 500,
                "scale": 1.0,
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        return f.name



def main():
    global executor, frame_worker, consumers, shm
    
    logger.info(f"Main process started. PID: {os.getpid()}")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run on exit
    atexit.register(cleanup_and_exit)

    parser = argparse.ArgumentParser(description="cvkit.io worker")
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--file', type=str, help='Path to video file for testing')
    parser.add_argument('--webcam', action='store_true', help='Use webcam for testing')
    parser.add_argument('--workers', type=int, help='Number of detect workers to spawn (overrides config)')
    
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
    
    # Get worker configuration
    workers_config = config_parser.get_workers_config()
    num_detect_workers = workers_config['detect_workers']
    
    # Override with CLI argument if provided
    if args.workers is not None:
        if args.workers > 0:
            num_detect_workers = args.workers
            logger.info(f"Worker count overridden by CLI argument: {args.workers}")
        else:
            logger.warning(f"Invalid worker count from CLI: {args.workers}. Using config/default.")
    
    logger.info(f"Using {num_detect_workers} detect workers")

    try:
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
                logger.info(f"Spawning FrameWorker and {num_detect_workers} "
                           f"DetectWorkers. PID: {os.getpid()}")
                producer = executor.submit(frame_worker.run)
                
                for i in range(num_detect_workers):
                    detect_worker = DetectWorker(work_queue, shm.name)
                    # Start multiple detect workers
                    consumers.append(executor.submit(detect_worker.run))
                
                # Wait for the result with timeout to allow interruption
                try:
                    global shutdown_requested
                    while not shutdown_requested:
                        try:
                            # Check producer with short timeout
                            producer.result(timeout=1.0)
                            break  # Producer finished normally
                        except TimeoutError:
                            continue  # Keep checking
                        
                    if not shutdown_requested:
                        # Wait for consumers to finish
                        for i, consumer in enumerate(consumers):
                            try:
                                consumer.result(timeout=5.0)
                            except TimeoutError:
                                logger.warning(f"Consumer {i} did not finish within timeout")
                                
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt caught in main loop")
                    shutdown_requested = True
                    
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        cleanup_and_exit(1)
        
    # Normal cleanup (should also be called by atexit)
    logger.info("All workers finished. Performing cleanup...")
    cleanup_and_exit(0)



if __name__ == "__main__":
    main()
