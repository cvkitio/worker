import argparse
import os
from config.parse_config import ConfigParser
from receiver.loader import ReceiverLoader
from detect.frame_worker import FrameWorker
from detect.detect_worker import DetectWorker
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, shared_memory

num_workers = 1  # Number of worker processes to spawn

def main():

    parser = argparse.ArgumentParser(description="cvkit.io worker")
    config_file = None
    if os.getenv("CVKIT_CONFIG") is not None:
        config_file = os.getenv("CVKIT_CONFIG")
    else:
        parser.add_argument('--config', type=str, help='Path to config file', required=True)
        args = parser.parse_args()
        config_file = args.config
    
    config_parser = ConfigParser(config_file)

    with Manager() as manager:
        # Shared memory can be used to share data between processes
        shm = shared_memory.SharedMemory(create=True, size=1024 * 1024 * 1024)  # 1MB shared memory
        
        work_queue = manager.Queue()
        # TODO use multiprocessing.shared_memory to share the queue between processes
        frame_worker = FrameWorker(config_parser.get_config(), work_queue, shm.name)
        
        
        
        with ProcessPoolExecutor() as executor:
            producer = executor.submit(frame_worker.run)
            
            consumers = []
            for i in range(num_workers):
                detect_worker = DetectWorker(work_queue, shm.name)
                # Start multiple detect workers
                consumers.append(executor.submit(detect_worker.run))
            # Wait for the result
            result = producer.result()
            for i in range(num_workers):
                consumer = consumers[i].result()

    frame_worker.unload()
    # Clean up shared memory
    shm.close()
    shm.unlink()  # Remove the shared memory block

if __name__ == "__main__":
    main()