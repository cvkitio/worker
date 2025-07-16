import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
from cvkitworker.detectors.frame_worker import FrameWorker
from cvkitworker.preprocessors.image_processing import resize_frame, convert_to_grayscale


class TestResizeAspectRatio:
    """Test the updated resize function that maintains aspect ratio."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "receivers": [],
            "detectors": [],
            "preprocessors": []
        }
        self.queue = Mock()
        self.shared_memory_name = "test_memory"
        self.frame_worker = FrameWorker(self.config, self.queue, self.shared_memory_name)
    
    def create_test_frame(self, width, height):
        """Create a test frame with specific dimensions."""
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    def test_resize_width_only(self):
        """Test resizing with only width specified."""
        # Create a 1920x1080 frame (16:9 aspect ratio)
        frame = self.create_test_frame(1920, 1080)
        
        # Resize to width 640, should maintain aspect ratio
        resized = resize_frame(frame, 640, None)
        
        # Expected height: 640 * (1080/1920) = 360
        assert resized.shape[1] == 640  # width
        assert resized.shape[0] == 360  # height
    
    def test_resize_height_only(self):
        """Test resizing with only height specified."""
        # Create a 1920x1080 frame (16:9 aspect ratio)
        frame = self.create_test_frame(1920, 1080)
        
        # Resize to height 720, should maintain aspect ratio
        resized = resize_frame(frame, None, 720)
        
        # Expected width: 720 * (1920/1080) = 1280
        assert resized.shape[1] == 1280  # width
        assert resized.shape[0] == 720   # height
    
    def test_resize_both_dimensions(self):
        """Test resizing with both width and height (old behavior)."""
        frame = self.create_test_frame(1920, 1080)
        
        # Resize to 640x480 (may distort)
        resized = resize_frame(frame, 640, 480)
        
        assert resized.shape[1] == 640  # width
        assert resized.shape[0] == 480  # height
    
    def test_resize_neither_dimension(self):
        """Test resizing with neither width nor height (returns original)."""
        frame = self.create_test_frame(1920, 1080)
        
        # No resize should return original frame
        resized = resize_frame(frame, None, None)
        
        assert resized.shape == frame.shape
        assert np.array_equal(resized, frame)
    
    def test_preprocess_frame_width_only(self):
        """Test preprocessing with resize config specifying only width."""
        self.config["preprocessors"] = [
            {
                "name": "resize",
                "type": "resize",
                "width": 800
                # height not specified
            }
        ]
        self.frame_worker.preprocessors = self.config["preprocessors"]
        
        frame = self.create_test_frame(1600, 1200)  # 4:3 aspect ratio
        processed = self.frame_worker.preprocess_frame(frame)
        
        # Expected: 800x600 (maintaining 4:3 ratio)
        assert processed.shape[1] == 800
        assert processed.shape[0] == 600
    
    def test_preprocess_frame_height_only(self):
        """Test preprocessing with resize config specifying only height."""
        self.config["preprocessors"] = [
            {
                "name": "resize",
                "type": "resize",
                "height": 600
                # width not specified
            }
        ]
        self.frame_worker.preprocessors = self.config["preprocessors"]
        
        frame = self.create_test_frame(1600, 1200)  # 4:3 aspect ratio
        processed = self.frame_worker.preprocess_frame(frame)
        
        # Expected: 800x600 (maintaining 4:3 ratio)
        assert processed.shape[1] == 800
        assert processed.shape[0] == 600
    
    def test_various_aspect_ratios(self):
        """Test resizing maintains aspect ratio for various frame sizes."""
        test_cases = [
            # (orig_width, orig_height, target_width, expected_height)
            (1920, 1080, 960, 540),    # 16:9 -> half size
            (1280, 720, 640, 360),     # 16:9 -> half size
            (640, 480, 320, 240),      # 4:3 -> half size
            (1000, 1000, 500, 500),    # 1:1 -> half size
            (2560, 1440, 1280, 720),   # 16:9 -> half size
        ]
        
        for orig_w, orig_h, target_w, expected_h in test_cases:
            frame = self.create_test_frame(orig_w, orig_h)
            resized = resize_frame(frame, target_w, None)
            
            assert resized.shape[1] == target_w
            assert resized.shape[0] == expected_h