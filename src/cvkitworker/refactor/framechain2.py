from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
import time
import os
from multiprocessing import Process, Queue, set_start_method
from multiprocessing import shared_memory


# --- Frame and Detection Definitions ---

@dataclass
class FrameInfo:
    shm_name: str
    shape: Tuple[int, ...]
    dtype: str
    timestamp: Optional[float] = None


@dataclass
class Detection:
    name: str
    polygon: List[Tuple[int, int]]
    metadata: Optional[dict] = None


# --- Base Processor Class ---

class Processor(ABC):
    @abstractmethod
    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        pass


# --- Subclasses of Processor ---

class PreProcessor(Processor):
    pass

class Detector(Processor):
    pass

class Markuper(Processor):
    pass

class Outputer(Processor):
    pass


# --- Sample Implementations ---

class Scale(PreProcessor):
    def __init__(self, scale_factor: float):
        self.scale_factor = scale_factor

    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        # Placeholder for scaling logic
        print(f"Scale {os.getpid()}")
        time.sleep(0.01)
        return frame, meta


class FaceDetector(Detector):
    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Optional[Detection]]:
        print(f"FaceDetect {os.getpid()}")
        time.sleep(0.2)
        return frame, Detection("face", [(10, 10), (100, 100)])


class FaceMarkup(Markuper):
    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        print(f"FaceMarkup {os.getpid()}")
        time.sleep(0.02)
        return frame, meta


class OutputFile(Outputer):
    def __init__(self, filename: str):
        self.filename = filename

    def process(self, frame: np.ndarray, meta: Any = None) -> Tuple[np.ndarray, Any]:
        print(f"Saving frame to {self.filename} {os.getpid()}")
        time.sleep(0.1)
        return frame, meta


# --- Processor Chain ---

class ProcessorChain:
    def __init__(self, processors: List[Processor]):
        self.processors = processors

    def run(self, frame: np.ndarray):
        meta = None
        for processor in self.processors:
            frame, meta = processor.process(frame, meta)
        return frame


# --- Producer and Consumer Functions using Shared Memory ---

def frame_producer(queue: Queue, num_frames: int, interval: float, shape, dtype, num_consumers: int):
    shm_list = []
    try:
        for i in range(num_frames):
            arr = np.random.randint(0, 255, shape, dtype=dtype)
            shm = shared_memory.SharedMemory(create=True, size=arr.nbytes)
            shm_arr = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
            np.copyto(shm_arr, arr)
            frame_info = FrameInfo(shm_name=shm.name, shape=shape, dtype=arr.dtype.name, timestamp=time.time())  # FIXED: use arr.dtype.name
            shm_list.append(shm)  # Keep reference to avoid premature GC
            print(f"Producer {os.getpid()} produced frame {i}")
            queue.put(frame_info)
            time.sleep(interval)
        # Signal consumers to stop
        for _ in range(num_consumers):
            queue.put(None)
        # Wait for consumers to finish processing
        time.sleep(2)
    finally:
        # Cleanup all shared memory blocks
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
        # Attach to shared memory
        shm = shared_memory.SharedMemory(name=frame_info.shm_name)
        arr = np.ndarray(frame_info.shape, dtype=frame_info.dtype, buffer=shm.buf)  # FIXED: pass dtype string
        print(f"Consumer {os.getpid()} processing frame at {frame_info.timestamp}")
        chain.run(arr)
        shm.close()  # Do not unlink here; producer will handle cleanup


# --- Example Main Function for Testing ---

if __name__ == "__main__":
    try:
        set_start_method("spawn")
    except RuntimeError:
        pass

    frame_queue = Queue(maxsize=10)
    num_frames = 30
    interval = 0.03  # 30ms
    shape = (480, 640, 3)
    dtype = np.uint8

    processor_chain = ProcessorChain([
        Scale(0.5),
        FaceDetector(),
        FaceMarkup(),
        OutputFile("output.jpg")
    ])

    # Start consumers
    num_consumers = 2
    consumers = [
        Process(target=frame_consumer, args=(frame_queue, processor_chain))
        for _ in range(num_consumers)
    ]
    for c in consumers:
        c.start()

    # Start producer
    producer = Process(target=frame_producer, args=(frame_queue, num_frames, interval, shape, dtype, num_consumers))
    producer.start()

    try:
        producer.join()
        for c in consumers:
            c.join()
    except KeyboardInterrupt:
        print("Interrupted! Attempting graceful shutdown...")
        producer.terminate()
        for c in consumers:
            c.terminate()
