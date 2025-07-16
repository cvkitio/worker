import cv2
from loguru import logger
import os
import platform


class ReceiverLoader:
    def __init__(self, receivers):
        self.receivers = receivers
        self.video_capture = None
        self.load()

    def load(self):
        logger.info(f"Receiver config: {self.receivers} (PID: {os.getpid()})")
        # Load the receiver configuration
        for config in self.receivers:
            if config["type"] == "rtsp":
                # Load RTSP receiver
                self.video_capture = cv2.VideoCapture(config["url"])
            elif config["type"] == "file":
                # Load file receiver
                file_path = config["source"]
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Video file not found: {file_path}")
                self.video_capture = cv2.VideoCapture(file_path)
                logger.info(f"Loaded video file: {file_path}")
            elif config["type"] == "webcam":
                # Load webcam receiver with improved macOS handling
                camera_index = config.get("source", 0)
                self.video_capture = self._create_camera_capture(camera_index)
                logger.info(f"Loaded webcam with index: {camera_index}")
            elif config["type"] == "http":
                # Load HTTP receiver
                # self.load_http_receiver(config)
                pass
            else:
                raise ValueError(f"Unknown receiver type: {config['type']}")
            # we will only deal with one receiver for now
            break

    def _enumerate_cameras(self):
        """Enumerate available camera devices for debugging."""
        available_cameras = []
        logger.debug("Enumerating available cameras...")
        
        for i in range(5):  # Check first 5 camera indices
            try:
                if platform.system() == "Darwin":
                    cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
                else:
                    cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    # Try to read a frame to verify the camera works
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        available_cameras.append({
                            'index': i,
                            'width': width,
                            'height': height,
                            'fps': fps
                        })
                        logger.debug(f"Camera {i}: {width}x{height} @ {fps}fps")
                cap.release()
            except Exception as e:
                logger.debug(f"Camera {i}: Not available ({e})")
        
        if available_cameras:
            logger.info(f"Found {len(available_cameras)} available camera(s): {[c['index'] for c in available_cameras]}")
        else:
            logger.warning("No cameras detected")
        
        return available_cameras

    def _create_camera_capture(self, camera_index):
        """Create camera capture with improved macOS handling."""
        logger.debug(f"Creating camera capture for index {camera_index} on {platform.system()}")
        
        # Enumerate cameras for debugging (only if explicitly requested)
        available_cameras = []
        if os.getenv('CVKIT_ENUMERATE_CAMERAS', '').lower() in ('true', '1', 'yes'):
            available_cameras = self._enumerate_cameras()
        
        # Try to create camera capture with platform-specific optimizations
        if platform.system() == "Darwin":  # macOS
            # Try with AVFoundation backend first (recommended for macOS)
            try:
                cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
                if cap.isOpened():
                    logger.info(f"Successfully opened camera {camera_index} with AVFoundation backend")
                    return cap
                else:
                    cap.release()
                    logger.warning(f"Failed to open camera {camera_index} with AVFoundation backend")
            except Exception as e:
                logger.warning(f"AVFoundation backend failed for camera {camera_index}: {e}")
        
        # Fallback to default backend or for non-macOS systems
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                logger.info(f"Successfully opened camera {camera_index} with default backend")
                return cap
            else:
                cap.release()
                logger.error(f"Failed to open camera {camera_index} with default backend")
        except Exception as e:
            logger.error(f"Default backend failed for camera {camera_index}: {e}")
        
        # Try alternative camera indices if the requested one fails
        alternative_indices = [0, 1, 2] if camera_index not in [0, 1, 2] else []
        for alt_index in alternative_indices:
            if alt_index != camera_index:
                logger.info(f"Trying alternative camera index {alt_index}")
                try:
                    if platform.system() == "Darwin":
                        cap = cv2.VideoCapture(alt_index, cv2.CAP_AVFOUNDATION)
                    else:
                        cap = cv2.VideoCapture(alt_index)
                    
                    if cap.isOpened():
                        logger.info(f"Successfully opened alternative camera {alt_index}")
                        return cap
                    else:
                        cap.release()
                except Exception as e:
                    logger.debug(f"Alternative camera {alt_index} failed: {e}")
        
        # If all attempts fail, raise an error
        raise RuntimeError(f"Failed to open any camera device. Tried index {camera_index} and alternatives {alternative_indices}")

    def get_video_capture(self):
        # Return the video capture object
        if self.video_capture is None:
            raise ValueError("Receiver not loaded")
        return self.video_capture

    def unload(self):
        # Unload the receiver configuration
        pass
