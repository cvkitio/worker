#!/usr/bin/env python3
"""
Test script to verify webcam scaling with aspect ratio preservation.
"""

import json
import tempfile
import sys
from pathlib import Path

# Add src to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cvkitworker.__main__ import create_webcam_config, create_file_config
from cvkitworker.detectors.frame_worker import FrameWorker
import numpy as np


def test_webcam_config_generation():
    """Test that webcam config is generated correctly."""
    print("Testing webcam config generation...")
    
    config_file = create_webcam_config()
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check that resize preprocessor is present
        preprocessors = config.get('preprocessors', [])
        resize_preprocessors = [p for p in preprocessors if p.get('type') == 'resize']
        
        if not resize_preprocessors:
            print("❌ No resize preprocessor found in webcam config")
            return False
            
        resize_config = resize_preprocessors[0]
        
        # Check that only width is specified (for aspect ratio preservation)
        if 'width' in resize_config and 'height' not in resize_config:
            print(f"✅ Webcam config correctly specifies only width: {resize_config['width']}")
            return True
        elif 'width' in resize_config and 'height' in resize_config:
            print(f"⚠️  Webcam config specifies both width and height (may distort): {resize_config}")
            return False
        else:
            print(f"❌ Webcam config has unexpected resize configuration: {resize_config}")
            return False
            
    finally:
        # Clean up temp file
        Path(config_file).unlink(missing_ok=True)


def test_file_config_generation():
    """Test that file config is generated correctly."""
    print("Testing file config generation...")
    
    # Create a dummy file for testing
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as dummy_file:
        dummy_file.write(b"dummy video content")
        dummy_path = dummy_file.name
    
    try:
        config_file = create_file_config(dummy_path)
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check that resize preprocessor is present
            preprocessors = config.get('preprocessors', [])
            resize_preprocessors = [p for p in preprocessors if p.get('type') == 'resize']
            
            if not resize_preprocessors:
                print("❌ No resize preprocessor found in file config")
                return False
                
            resize_config = resize_preprocessors[0]
            
            # Check that only width is specified (for aspect ratio preservation)
            if 'width' in resize_config and 'height' not in resize_config:
                print(f"✅ File config correctly specifies only width: {resize_config['width']}")
                return True
            elif 'width' in resize_config and 'height' in resize_config:
                print(f"⚠️  File config specifies both width and height (may distort): {resize_config}")
                return False
            else:
                print(f"❌ File config has unexpected resize configuration: {resize_config}")
                return False
                
        finally:
            # Clean up temp config file
            Path(config_file).unlink(missing_ok=True)
            
    finally:
        # Clean up dummy video file
        Path(dummy_path).unlink(missing_ok=True)


def test_aspect_ratio_logic():
    """Test the aspect ratio preservation logic directly."""
    print("Testing aspect ratio preservation logic...")
    
    # Create a mock frame worker to test the resize logic
    mock_config = {
        "receivers": [],
        "detectors": [],
        "preprocessors": []
    }
    
    frame_worker = FrameWorker(mock_config, None, "test_memory")
    
    # Test different input sizes and expected outputs
    test_cases = [
        # (input_width, input_height, target_width, expected_height)
        (1920, 1080, 640, 360),   # 16:9 -> 640x360
        (1280, 720, 640, 360),    # 16:9 -> 640x360
        (640, 480, 320, 240),     # 4:3 -> 320x240
        (1000, 1000, 500, 500),   # 1:1 -> 500x500
    ]
    
    all_passed = True
    
    for input_w, input_h, target_w, expected_h in test_cases:
        # Create a test frame
        test_frame = np.zeros((input_h, input_w, 3), dtype=np.uint8)
        
        # Test resize with only width specified
        resized = frame_worker._resize_frame(test_frame, target_w, None)
        
        actual_h, actual_w = resized.shape[:2]
        
        if actual_w == target_w and actual_h == expected_h:
            print(f"✅ {input_w}x{input_h} -> {actual_w}x{actual_h} (expected {target_w}x{expected_h})")
        else:
            print(f"❌ {input_w}x{input_h} -> {actual_w}x{actual_h} (expected {target_w}x{expected_h})")
            all_passed = False
    
    return all_passed


if __name__ == "__main__":
    print("=== Webcam Scaling Test ===\n")
    
    webcam_ok = test_webcam_config_generation()
    file_ok = test_file_config_generation()
    aspect_ok = test_aspect_ratio_logic()
    
    print(f"\n=== Results ===")
    print(f"Webcam config: {'✅ PASS' if webcam_ok else '❌ FAIL'}")
    print(f"File config: {'✅ PASS' if file_ok else '❌ FAIL'}")  
    print(f"Aspect ratio logic: {'✅ PASS' if aspect_ok else '❌ FAIL'}")
    
    if webcam_ok and file_ok and aspect_ok:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Some tests FAILED!")
        sys.exit(1)