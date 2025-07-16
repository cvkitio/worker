#!/usr/bin/env python3
"""
FrameChain - Multi-processor frame processing pipeline
"""
from multiprocessing import Process, Queue, set_start_method
import numpy as np
import time

from framechain.core import ProcessorChain, frame_producer, frame_consumer
from framechain.preprocessors import Scale
from framechain.detectors import FaceDetector
from framechain.markupers import FaceMarkup
from framechain.outputers import OutputFile


def main():
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

    num_consumers = 2
    consumers = [
        Process(target=frame_consumer, args=(frame_queue, processor_chain))
        for _ in range(num_consumers)
    ]
    for c in consumers:
        c.start()

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


if __name__ == "__main__":
    main()