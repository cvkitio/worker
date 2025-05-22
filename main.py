import argparse
from config.parse_config import ConfigParser
from receiver.loader import ReceiverLoader
from detect.worker import FrameWorker
import cv2

def main():
    parser = argparse.ArgumentParser(description="A simple argument parser.")
    parser.add_argument('--config', type=str, help='Path to config file', required=True)

    args = parser.parse_args()
    
    # Parse the config file
    config_parser = ConfigParser(args.config)
    
    # Open the receiver from the config file    
    receiver = ReceiverLoader(config_parser.config["receivers"])

    frame_worker = FrameWorker(receiver, config_parser.config["detectors"])
    frame_worker.run()

    receiver.get_video_capture().release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()