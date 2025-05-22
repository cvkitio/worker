import argparse
from config.parse_config import ConfigParser
from receiver.loader import ReceiverLoader
from detect.frame_worker import FrameWorker
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager


def main():
    parser = argparse.ArgumentParser(description="A simple argument parser.")
    parser.add_argument('--config', type=str, help='Path to config file', required=True)

    args = parser.parse_args()
    
    # Parse the config file
    config_parser = ConfigParser(args.config)

    frame_worker = FrameWorker(config_parser.config)
    
    with Manager() as manager:
        work_queue = manager.Queue()
        with ProcessPoolExecutor() as executor:
            # Submit the frame worker to the executor
            future = executor.submit(frame_worker.run)
            # Wait for the result
            result = future.result()

    
    frame_worker.unload()

if __name__ == "__main__":
    main()