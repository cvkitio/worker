#!/usr/bin/env python3
"""
Test cases for timing measurement functionality.
"""

import unittest
import os
import json
import tempfile
import time
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.utils.timing import (
    TimingManager,
    FileTimingStorage, 
    DatabaseTimingStorage,
    TelemetryTimingStorage,
    measure_timing,
    measure_face_detection,
    measure_color_conversion,
    measure_scaling,
    get_timing_manager
)


class TestTimingStorage(unittest.TestCase):
    """Test timing storage implementations."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_timing.jsonl')
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_timing_storage(self):
        """Test file-based timing storage."""
        storage = FileTimingStorage(self.temp_file)
        
        # Test storing measurements
        measurement1 = {
            'timestamp': '2025-06-13T08:00:00',
            'function': 'test_func',
            'duration_ms': 100.5,
            'process_id': 12345,
            'context': {'test': 'data'}
        }
        
        measurement2 = {
            'timestamp': '2025-06-13T08:00:01',
            'function': 'another_func',
            'duration_ms': 25.3,
            'process_id': 12345,
            'context': {'other': 'data'}
        }
        
        storage.store_timing(measurement1)
        storage.store_timing(measurement2)
        storage.flush()
        storage.close()
        
        # Verify file contents
        self.assertTrue(os.path.exists(self.temp_file))
        
        with open(self.temp_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 2)
        
        # Verify JSON parsing
        parsed1 = json.loads(lines[0])
        parsed2 = json.loads(lines[1])
        
        self.assertEqual(parsed1['function'], 'test_func')
        self.assertEqual(parsed1['duration_ms'], 100.5)
        self.assertEqual(parsed2['function'], 'another_func')
        self.assertEqual(parsed2['duration_ms'], 25.3)
    
    def test_database_timing_storage_placeholder(self):
        """Test database storage placeholder."""
        storage = DatabaseTimingStorage("test_connection")
        
        # Should not raise errors but also not actually store
        measurement = {
            'timestamp': '2025-06-13T08:00:00',
            'function': 'test_func',
            'duration_ms': 100.5,
            'process_id': 12345
        }
        
        storage.store_timing(measurement)
        storage.flush()
        storage.close()
    
    def test_telemetry_timing_storage_placeholder(self):
        """Test telemetry storage placeholder."""
        storage = TelemetryTimingStorage("http://test.endpoint", "test_key")
        
        # Should not raise errors but also not actually store
        measurement = {
            'timestamp': '2025-06-13T08:00:00',
            'function': 'test_func', 
            'duration_ms': 100.5,
            'process_id': 12345
        }
        
        storage.store_timing(measurement)
        storage.flush()
        storage.close()


class TestTimingManager(unittest.TestCase):
    """Test timing manager functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_timing.jsonl')
        
        # Clear any existing global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear environment variables
        for key in ['CVKIT_TIMING_ENABLED', 'CVKIT_TIMING_STORAGE', 'CVKIT_TIMING_FILE']:
            if key in os.environ:
                del os.environ[key]
        
        # Reset global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def test_timing_disabled_by_default(self):
        """Test timing is disabled by default."""
        manager = TimingManager()
        self.assertFalse(manager.enabled)
        self.assertIsNone(manager.storage)
    
    def test_timing_enabled_by_environment(self):
        """Test timing enabled via environment variable."""
        os.environ['CVKIT_TIMING_ENABLED'] = 'true'
        os.environ['CVKIT_TIMING_FILE'] = self.temp_file
        
        manager = TimingManager()
        self.assertTrue(manager.enabled)
        self.assertIsNotNone(manager.storage)
        self.assertIsInstance(manager.storage, FileTimingStorage)
    
    def test_timing_disabled_by_environment(self):
        """Test timing explicitly disabled via environment variable."""
        os.environ['CVKIT_TIMING_ENABLED'] = 'false'
        
        manager = TimingManager()
        self.assertFalse(manager.enabled)
        self.assertIsNone(manager.storage)
    
    def test_timing_record_when_enabled(self):
        """Test recording timing when enabled."""
        os.environ['CVKIT_TIMING_ENABLED'] = 'true'
        os.environ['CVKIT_TIMING_FILE'] = self.temp_file
        
        manager = TimingManager()
        
        # Record a timing measurement
        context = {'test': 'data', 'args': [1, 2, 3]}
        manager.record_timing('test_function', 123.45, context)
        manager.flush()
        
        # Verify file was created and contains data
        self.assertTrue(os.path.exists(self.temp_file))
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'test_function')
        self.assertEqual(measurement['duration_ms'], 123.45)
        self.assertEqual(measurement['context']['test'], 'data')
        self.assertEqual(measurement['process_id'], os.getpid())
    
    def test_timing_no_record_when_disabled(self):
        """Test no recording when disabled."""
        os.environ['CVKIT_TIMING_ENABLED'] = 'false'
        
        manager = TimingManager()
        
        # Try to record (should be ignored)
        manager.record_timing('test_function', 123.45)
        manager.flush()
        
        # File should not exist
        self.assertFalse(os.path.exists(self.temp_file))
    
    def test_storage_backend_selection(self):
        """Test different storage backend selection."""
        os.environ['CVKIT_TIMING_ENABLED'] = 'true'
        
        # Test file storage (default)
        os.environ['CVKIT_TIMING_STORAGE'] = 'file'
        manager = TimingManager()
        self.assertIsInstance(manager.storage, FileTimingStorage)
        
        # Reset manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
        
        # Test database storage
        os.environ['CVKIT_TIMING_STORAGE'] = 'database'
        manager = TimingManager()
        self.assertIsInstance(manager.storage, DatabaseTimingStorage)
        
        # Reset manager
        cvkitworker.utils.timing._timing_manager = None
        
        # Test telemetry storage
        os.environ['CVKIT_TIMING_STORAGE'] = 'telemetry'
        manager = TimingManager()
        self.assertIsInstance(manager.storage, TelemetryTimingStorage)


class TestTimingDecorators(unittest.TestCase):
    """Test timing decorator functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_timing.jsonl')
        
        # Enable timing
        os.environ['CVKIT_TIMING_ENABLED'] = 'true'
        os.environ['CVKIT_TIMING_FILE'] = self.temp_file
        
        # Clear global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear environment variables
        for key in ['CVKIT_TIMING_ENABLED', 'CVKIT_TIMING_STORAGE', 'CVKIT_TIMING_FILE']:
            if key in os.environ:
                del os.environ[key]
        
        # Reset global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def test_basic_timing_decorator(self):
        """Test basic timing decorator."""
        @measure_timing("test_function")
        def test_func():
            time.sleep(0.01)  # 10ms
            return "result"
        
        result = test_func()
        self.assertEqual(result, "result")
        
        # Check timing file
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'test_function')
        self.assertGreaterEqual(measurement['duration_ms'], 8)  # Allow some variance
        self.assertLessEqual(measurement['duration_ms'], 20)
    
    def test_timing_decorator_with_args(self):
        """Test timing decorator with argument capture."""
        @measure_timing("test_with_args", include_args=True, include_result=True)
        def test_func(a, b, keyword=None):
            return f"{a}_{b}_{keyword}"
        
        result = test_func("hello", 123, keyword="world")
        self.assertEqual(result, "hello_123_world")
        
        # Check timing file
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'test_with_args')
        self.assertIn('args', measurement['context'])
        self.assertIn('kwargs', measurement['context'])
        self.assertEqual(measurement['context']['args'], ["hello", 123])
        self.assertEqual(measurement['context']['kwargs'], {"keyword": "world"})
    
    def test_face_detection_decorator(self):
        """Test face detection specific decorator."""
        @measure_face_detection
        def mock_detect(frame):
            # Simulate face detection
            time.sleep(0.005)  # 5ms
            return [
                {'x': 100, 'y': 100, 'width': 50, 'height': 50, 'confidence': 0.9},
                {'x': 200, 'y': 150, 'width': 45, 'height': 48, 'confidence': 0.8}
            ]
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = mock_detect(frame)
        
        self.assertEqual(len(faces), 2)
        
        # Check timing file
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'face_detection')
        self.assertEqual(measurement['context']['result_length'], 2)
        self.assertIn('args', measurement['context'])
    
    def test_color_conversion_decorator(self):
        """Test color conversion decorator."""
        @measure_color_conversion
        def mock_convert(frame, conversion_code):
            # Simulate color conversion
            time.sleep(0.002)  # 2ms
            return np.zeros_like(frame)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = mock_convert(frame, 123)
        
        self.assertEqual(result.shape, frame.shape)
        
        # Check timing file
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'color_conversion')
    
    def test_scaling_decorator(self):
        """Test scaling decorator."""
        @measure_scaling
        def mock_resize(frame, width, height):
            # Simulate scaling
            time.sleep(0.003)  # 3ms
            return np.zeros((height, width, 3), dtype=np.uint8)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = mock_resize(frame, 320, 240)
        
        self.assertEqual(result.shape, (240, 320, 3))
        
        # Check timing file
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'scaling')
    
    def test_timing_disabled_no_overhead(self):
        """Test that disabled timing has no significant overhead."""
        # Disable timing
        os.environ['CVKIT_TIMING_ENABLED'] = 'false'
        
        # Reset timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
        
        @measure_timing("disabled_test")
        def test_func():
            return "result"
        
        # Function should work normally
        result = test_func()
        self.assertEqual(result, "result")
        
        # No timing file should be created
        self.assertFalse(os.path.exists(self.temp_file))
    
    def test_exception_handling_in_timing(self):
        """Test timing decorator handles exceptions properly."""
        @measure_timing("exception_test")
        def failing_func():
            raise ValueError("Test exception")
        
        # Exception should still be raised
        with self.assertRaises(ValueError):
            failing_func()
        
        # But timing should still be recorded
        manager = get_timing_manager()
        manager.flush()
        
        with open(self.temp_file, 'r') as f:
            line = f.readline()
        
        measurement = json.loads(line)
        self.assertEqual(measurement['function'], 'exception_test')
        self.assertGreater(measurement['duration_ms'], 0)


class TestIntegrationWithCV(unittest.TestCase):
    """Test integration with actual CV functions."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test_timing.jsonl')
        
        # Enable timing
        os.environ['CVKIT_TIMING_ENABLED'] = 'true'
        os.environ['CVKIT_TIMING_FILE'] = self.temp_file
        
        # Clear global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear environment variables
        for key in ['CVKIT_TIMING_ENABLED', 'CVKIT_TIMING_STORAGE', 'CVKIT_TIMING_FILE']:
            if key in os.environ:
                del os.environ[key]
        
        # Reset global timing manager
        import cvkitworker.utils.timing
        cvkitworker.utils.timing._timing_manager = None
    
    def test_face_detector_timing_integration(self):
        """Test timing integration with actual FaceDetector."""
        try:
            from cvkitworker.detectors.detectors.face_detect import FaceDetector
            
            # Create detector (this will test model loading timing too)
            detector = FaceDetector("dlib")
            
            # Create test frame
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            
            # Run detection (this should be timed)
            faces = detector.detect(frame)
            
            # Flush timing data
            manager = get_timing_manager()
            manager.flush()
            
            # Check timing file exists and has measurements
            self.assertTrue(os.path.exists(self.temp_file))
            
            with open(self.temp_file, 'r') as f:
                lines = f.readlines()
            
            # Should have at least the face detection measurement
            self.assertGreater(len(lines), 0)
            
            # Check for face detection timing
            measurements = [json.loads(line) for line in lines]
            face_detection_measurements = [
                m for m in measurements 
                if m['function'] == 'face_detection'
            ]
            
            self.assertGreater(len(face_detection_measurements), 0)
            
            # Verify measurement structure
            measurement = face_detection_measurements[0]
            self.assertIn('duration_ms', measurement)
            self.assertIn('timestamp', measurement)
            self.assertIn('process_id', measurement)
            self.assertIn('context', measurement)
            
        except ImportError:
            self.skipTest("FaceDetector not available for testing")


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestTimingStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestTimingManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTimingDecorators))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithCV))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)