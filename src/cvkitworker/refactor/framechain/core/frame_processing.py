from multiprocessing import Queue, shared_memory
import numpy as np
import time
import os
from ..models import FrameInfo
from .processor_chain import ProcessorChain


def frame_producer(queue: Queue, num_frames: int, interval: float, shape, dtype, num_consumers: int):
    shm_list = []
    try:
        for i in range(num_frames):
            arr = np.random.randint(0, 255, shape, dtype=dtype)
            shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
            shm_arr = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
            np.copyto(shm_arr, arr)
            frame_info = FrameInfo(shm_name=shm.name, shape=shape, dtype=arr.dtype.name, timestamp=time.time())
            shm_list.append(shm)
            print(f"Producer {os.getpid()} produced frame {i}")
            queue.put(frame_info)
            time.sleep(interval)
        
        for _ in range(num_consumers):
            queue.put(None)
        
        time.sleep(2)
    finally:
        for shm in shm_list:
            try:
                shm.close()
                shm.unlink()
            except FileNotFoundError:
                pass


def frame_consumer(queue: Queue, chain: ProcessorChain):
    while True:
        frame_info = queue.get()
        if frame_info is None:
            print(f"Consumer {os.getpid()} exiting.")
            break
        
        shm = shared_memory.SharedMemory(name=frame_info.shm_name)
        arr = np.ndarray(frame_info.shape, dtype=frame_info.dtype, buffer=shm.buf)
        print(f"Consumer {os.getpid()} processing frame at {frame_info.timestamp}")
        chain.run(arr)
        shm.close()