# The worker plugin is responsible for running the detection process in a separate process.
import cv2
import time

class FrameWorker:
    def __init__(self, receiver, detectors):
        self.receiver = receiver
        self.detectors = detectors
        self.video_capture = None
        self.load()

    def load(self):
        # Load the receiver configuration
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
        last_processed_time = time.time()
        while self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if not ret:
                print("Failed to retrieve frame")
                break
            
            detectors = self.get_root_detectors()
            elapsed_time = (time.time() - last_processed_time) * 1000  # Convert to milliseconds
            for detector in detectors:
                # Process the frame with the detector
                # For now, we will just print the detector name
                if elapsed_time > float(detector["frequency_ms"]):
                    last_processed_time = time.time()
                    print(f"Processing with detector: {detector['name']}")
                    

            # Process the frame (e.g., run detection)
            # For now, we will just display the frame
            cv2.imshow('RTSP Stream', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.unload()

    def unload(self):
        # Unload the receiver configuration
        if self.video_capture is not None:
            self.video_capture.release()
        cv2.destroyAllWindows()

