import time
import os

class DetectWorker:
    def __init__(self, queue):
        self.queue = queue

    def run(self):
        print(f"DetectWorker started, waiting for items in the queue... pid: {os.getpid()}")
        while True:
            if not self.queue.empty():
                item = self.queue.get()
                if item == "STOP":
                    break
                print(f"{os.getpid()} Processing item from queue: {item} ")
            else:
                time.sleep(0.1)