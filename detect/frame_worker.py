# The worker plugin is responsible for running the detection process in a separate process.
import cv2
import time

from detect.loader import DetectorLoader
from receiver.loader import ReceiverLoader

class FrameWorker:
    def __init__(self, config, queue):
        self.receiver_config = config["receivers"]
        self.detectors = config["detectors"]
        self.video_capture = None
        self.receiver = None
        self.queue = queue
        
    def load(self):
        # Load the receiver configuration
        self.receiver = ReceiverLoader(self.receiver_config)
        self.video_capture = self.receiver.get_video_capture()
        if not self.video_capture.isOpened():
            raise ValueError("Failed to open video capture")
        
    def get_root_detectors(self):
        detectors = []
        for detector in self.detectors:
            if "parent" not in detector or detector["parent"] == None:
                detectors.append(detector)
        return detectors
        
    def run(self):
        print(f"FrameWorker started pid: {os.getpid()}")
        self.load()
        # Ideally what we want to do is have each type of detector already loaded
        # and then we can just call detector.detect(frame)
        detectors = self.get_root_detectors()
        detector_runner = DetectorLoader(detectors)
        
        last_processed_time = time.time()
        while self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if not ret:
                print("Failed to retrieve frame")
                # TODO add retry logic and then exit
                break
            
            
            elapsed_time = (time.time() - last_processed_time) * 1000  # Convert to milliseconds
            for detector in detectors:
                if elapsed_time > float(detector["frequency_ms"]):
                    last_processed_time = time.time()
                    self.queue.put(f"{detector['name']}")
                    print(f"Sent to queue: {detector['name']}")
                    

            # Process the frame (e.g., run detection)
            # For now, we will just display the frame
            cv2.imshow('RTSP Stream', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.unload()

    def unload(self):
        # Unload the receiver configuration
        self.queue.put("STOP")
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

