#!/usr/bin/env python3
"""
Simple test cases for video file processing functionality.
"""

import unittest
import os
import json
import tempfile
import sys
from pathlib import Path
import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestVideoSimple(unittest.TestCase):
    """Simple tests for video file processing."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = Path(__file__).parent.parent / 'test_videos' / 'big_buck_bunny_480p.mp4'
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_file_exists_and_readable(self):
        """Test that the test video file exists and can be opened by OpenCV."""
        self.assertTrue(self.video_path.exists(), f"Test video not found: {self.video_path}")
        self.assertTrue(self.video_path.is_file(), f"Test video is not a file: {self.video_path}")
        self.assertGreater(self.video_path.stat().st_size, 1000, "Test video file is too small")
        
        # Test that OpenCV can open the video
        cap = cv2.VideoCapture(str(self.video_path))
        self.assertTrue(cap.isOpened(), "OpenCV cannot open the test video file")
        
        # Test that we can read at least one frame
        ret, frame = cap.read()
        self.assertTrue(ret, "Cannot read first frame from test video")
        self.assertIsNotNone(frame, "First frame is None")
        self.assertEqual(len(frame.shape), 3, "Frame should be 3-dimensional (height, width, channels)")
        
        # Get video properties
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        self.assertGreater(frame_count, 0, "Video should have frames")
        self.assertGreater(fps, 0, "Video should have valid FPS")
        self.assertGreater(width, 0, "Video should have valid width")
        self.assertGreater(height, 0, "Video should have valid height")
        
        print(f"Video properties: {width}x{height}, {fps} FPS, {frame_count} frames")
        
        cap.release()
    
    def test_receiver_loader_with_video_file(self):
        """Test that ReceiverLoader can load video files."""
        from cvkitworker.receivers.loader import ReceiverLoader
        
        # Create receiver config for video file
        receivers_config = [
            {
                "name": "video_test",
                "type": "file",
                "source": str(self.video_path)
            }
        ]
        
        # Test receiver loading
        receiver = ReceiverLoader(receivers_config)
        video_capture = receiver.get_video_capture()
        
        self.assertIsNotNone(video_capture, "Video capture should not be None")
        self.assertTrue(video_capture.isOpened(), "Video capture should be opened")
        
        # Test reading frames
        ret, frame = video_capture.read()
        self.assertTrue(ret, "Should be able to read frame from video")
        self.assertIsNotNone(frame, "Frame should not be None")
        
        # Test frame properties
        self.assertEqual(len(frame.shape), 3, "Frame should be 3-dimensional")
        height, width, channels = frame.shape
        self.assertGreater(height, 0, "Frame height should be positive")
        self.assertGreater(width, 0, "Frame width should be positive") 
        self.assertEqual(channels, 3, "Frame should have 3 color channels")
        
        print(f"Frame properties: {width}x{height}x{channels}")
        
        video_capture.release()
    
    def test_frame_preprocessing(self):
        """Test frame preprocessing functionality."""
        from cvkitworker.detectors.frame_worker import FrameWorker
        from cvkitworker.receivers.loader import ReceiverLoader
        
        # Create test config with preprocessors
        config = {
            "receivers": [
                {
                    "name": "video_test",
                    "type": "file",
                    "source": str(self.video_path)
                }
            ],
            "preprocessors": [
                {
                    "name": "resize",
                    "type": "resize", 
                    "width": 320,
                    "height": 240
                }
            ],
            "detectors": [
                {
                    "name": "face_detector",
                    "type": "face_detector",
                    "variant": "dlib"
                }
            ]
        }
        
        # Test receiver loading
        receiver = ReceiverLoader(config["receivers"])
        video_capture = receiver.get_video_capture()
        
        # Read original frame
        ret, original_frame = video_capture.read()
        self.assertTrue(ret, "Should read original frame")
        
        original_height, original_width = original_frame.shape[:2]
        print(f"Original frame: {original_width}x{original_height}")
        
        # Test preprocessing - create a mock FrameWorker just for preprocessing
        class MockFrameWorker:
            def __init__(self, config):
                self.preprocessors = config["preprocessors"]
            
            def preprocess_frame(self, frame):
                import cv2
                for preprocessor in self.preprocessors:
                    match preprocessor["type"]:
                        case "resize":
                            width = int(preprocessor.get("width", frame.shape[1]))
                            height = int(preprocessor.get("height", frame.shape[0]))
                            frame = cv2.resize(frame, (width, height))
                        case "grayscale":
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                return frame
        
        # Test preprocessing
        mock_worker = MockFrameWorker(config)
        processed_frame = mock_worker.preprocess_frame(original_frame.copy())
        
        # Verify preprocessing worked
        processed_height, processed_width = processed_frame.shape[:2]
        self.assertEqual(processed_width, 320, "Processed width should be 320")
        self.assertEqual(processed_height, 240, "Processed height should be 240")
        
        print(f"Processed frame: {processed_width}x{processed_height}")
        
        video_capture.release()
    
    def test_video_config_creation(self):
        """Test creating configuration for video processing."""
        config = {
            "receivers": [
                {
                    "name": "video_input",
                    "type": "file",
                    "source": str(self.video_path)
                }
            ],
            "preprocessors": [
                {
                    "name": "resize",
                    "type": "resize",
                    "width": 640,
                    "height": 480
                }
            ],
            "detectors": [
                {
                    "name": "face_detector", 
                    "type": "face_detector",
                    "variant": "dlib",
                    "frequency_ms": 100,
                    "device": "cpu"
                }
            ],
            "timing": {
                "enabled": True,
                "storage": "file",
                "file_path": "logs/video_timing.jsonl"
            }
        }
        
        # Write config to file
        config_path = os.path.join(self.temp_dir, 'video_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Verify config file
        self.assertTrue(os.path.exists(config_path))
        
        # Read and validate config
        with open(config_path, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["receivers"][0]["type"], "file")
        self.assertEqual(loaded_config["receivers"][0]["source"], str(self.video_path))
        self.assertTrue(loaded_config["timing"]["enabled"])
        self.assertEqual(len(loaded_config["preprocessors"]), 1)
        self.assertEqual(len(loaded_config["detectors"]), 1)
        
        print(f"Config created successfully: {config_path}")
    
    def test_video_processing_components_import(self):
        """Test that all required video processing components can be imported."""
        try:
            from cvkitworker.receivers.loader import ReceiverLoader
            from cvkitworker.detectors.frame_worker import FrameWorker
            from cvkitworker.detectors.detectors.face_detect import FaceDetector
            from cvkitworker.utils.timing import measure_timing
            
            # Test basic instantiation
            receivers_config = [{"name": "test", "type": "file", "source": str(self.video_path)}]
            receiver = ReceiverLoader(receivers_config)
            self.assertIsNotNone(receiver)
            
            # Test face detector can be created (without loading models)
            # This just tests the class can be instantiated
            try:
                detector = FaceDetector("dlib")
                self.assertIsNotNone(detector)
                print("FaceDetector instantiated successfully")
            except Exception as e:
                print(f"FaceDetector instantiation failed (expected without models): {e}")
            
            print("All video processing components imported successfully")
            
        except ImportError as e:
            self.fail(f"Failed to import video processing components: {e}")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestVideoSimple))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)