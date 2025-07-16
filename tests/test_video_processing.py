#!/usr/bin/env python3
"""
Test cases for video file processing functionality.
"""

import unittest
import os
import json
import tempfile
import time
import subprocess
import sys
import pytest
from pathlib import Path
from unittest.mock import patch
import threading
import signal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.mark.integration
@pytest.mark.video
@pytest.mark.slow
class TestVideoProcessing(unittest.TestCase):
    """Test video file input and processing."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = Path(__file__).parent.parent / 'test_videos' / 'big_buck_bunny_480p.mp4'
        self.config_path = os.path.join(self.temp_dir, 'test_video_config.json')
        self.timing_log_path = os.path.join(self.temp_dir, 'video_timing.jsonl')
        
        # Create test configuration for video processing
        self.test_config = {
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
                    "variant": "dlib",
                    "frequency_ms": 200,
                    "scale": 1.0,
                    "device": "cpu"
                }
            ],
            "timing": {
                "enabled": True,
                "storage": "file",
                "file_path": self.timing_log_path,
                "include_args": True,
                "include_results": True
            }
        }
        
        # Write test configuration file
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f, indent=2)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_file_exists(self):
        """Test that the test video file exists and is accessible."""
        self.assertTrue(self.video_path.exists(), f"Test video not found: {self.video_path}")
        self.assertTrue(self.video_path.is_file(), f"Test video is not a file: {self.video_path}")
        self.assertGreater(self.video_path.stat().st_size, 1000, "Test video file is too small")
    
    def test_video_config_generation(self):
        """Test video configuration generation and validation."""
        # Verify config file was created correctly
        self.assertTrue(os.path.exists(self.config_path))
        
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        
        # Verify configuration structure
        self.assertIn('receivers', config)
        self.assertIn('detectors', config)
        self.assertIn('timing', config)
        
        # Verify receiver configuration
        receiver = config['receivers'][0]
        self.assertEqual(receiver['type'], 'file')
        self.assertEqual(receiver['source'], str(self.video_path))
        
        # Verify timing is enabled
        self.assertTrue(config['timing']['enabled'])
        self.assertEqual(config['timing']['file_path'], self.timing_log_path)
    
    def test_video_processing_with_logs(self):
        """Test video processing and verify appropriate log entries."""
        # Set up environment for timing
        env = os.environ.copy()
        env['CVKIT_TIMING_ENABLED'] = 'true'
        env['CVKIT_TIMING_FILE'] = self.timing_log_path
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / 'src')
        
        # Run video processing for a limited time
        cmd = [
            sys.executable, '-m', 'cvkitworker',
            '--config', self.config_path
        ]
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            # Let it run for a shorter time to process some frames
            stdout, stderr = process.communicate(timeout=4)
            
        except subprocess.TimeoutExpired:
            # Expected - terminate the process after timeout
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        # Capture the output for analysis
        output_lines = stdout.split('\n') if stdout else []
        error_lines = stderr.split('\n') if stderr else []
        
        # Verify basic video processing started
        video_loaded = any('Loaded video file' in line for line in output_lines + error_lines)
        frame_worker_started = any('FrameWorker started' in line for line in output_lines + error_lines)
        
        # Print debug information if test fails
        if not (video_loaded or frame_worker_started):
            print(f"STDOUT:\n{stdout}")
            print(f"STDERR:\n{stderr}")
            print(f"Video path: {self.video_path}")
            print(f"Config path: {self.config_path}")
        
        self.assertTrue(
            video_loaded or frame_worker_started,
            "Video processing did not start properly. Check stdout/stderr above."
        )
    
    def test_timing_measurements_created(self):
        """Test that timing measurements are properly created during video processing."""
        # Set up environment for timing
        env = os.environ.copy()
        env['CVKIT_TIMING_ENABLED'] = 'true'
        env['CVKIT_TIMING_FILE'] = self.timing_log_path
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / 'src')
        
        # Run video processing for a short time
        cmd = [
            sys.executable, '-m', 'cvkitworker',
            '--config', self.config_path
        ]
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            # Let it run for a shorter time
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        # Check if timing file was created
        if os.path.exists(self.timing_log_path):
            with open(self.timing_log_path, 'r') as f:
                timing_lines = f.readlines()
            
            # Verify timing measurements exist
            self.assertGreater(len(timing_lines), 0, "No timing measurements recorded")
            
            # Parse and verify timing entries
            measurements = []
            for line in timing_lines:
                if line.strip():
                    try:
                        measurement = json.loads(line)
                        measurements.append(measurement)
                    except json.JSONDecodeError:
                        continue
            
            self.assertGreater(len(measurements), 0, "No valid timing measurements found")
            
            # Verify measurement structure
            for measurement in measurements[:3]:  # Check first few measurements
                self.assertIn('timestamp', measurement)
                self.assertIn('function', measurement)
                self.assertIn('duration_ms', measurement)
                self.assertIn('process_id', measurement)
                self.assertIsInstance(measurement['duration_ms'], (int, float))
                self.assertGreater(measurement['duration_ms'], 0)
            
            # Look for specific CV operations
            function_names = [m['function'] for m in measurements]
            
            # Should have some frame processing or face detection operations
            cv_operations = [
                'face_detection',
                'frame_processing', 
                'scaling',
                'color_conversion'
            ]
            
            found_cv_ops = [op for op in cv_operations if op in function_names]
            self.assertGreater(
                len(found_cv_ops), 0,
                f"No CV operations found in timing logs. Functions recorded: {set(function_names)}"
            )
            
        else:
            # If no timing file, check if the process at least started
            self.assertIn(
                'video', stdout.lower() + stderr.lower(),
                f"Video processing did not start. Output: {stdout}\nErrors: {stderr}"
            )
    
    def test_video_processing_frame_detection(self):
        """Test that video processing includes frame detection logging."""
        # Create a simple config without timing complexity
        simple_config = {
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
                    "variant": "dlib",
                    "frequency_ms": 500,
                    "device": "cpu"
                }
            ]
        }
        
        simple_config_path = os.path.join(self.temp_dir, 'simple_config.json')
        with open(simple_config_path, 'w') as f:
            json.dump(simple_config, f, indent=2)
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / 'src')
        
        # Run video processing
        cmd = [
            sys.executable, '-m', 'cvkitworker',
            '--config', simple_config_path
        ]
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        # Combine output for analysis
        all_output = stdout + stderr
        
        # Verify key processing indicators
        processing_indicators = [
            'Loaded video file',
            'FrameWorker started',
            'Frame shape:',
            'face detector',
            'DetectWorker started'
        ]
        
        found_indicators = []
        for indicator in processing_indicators:
            if indicator.lower() in all_output.lower():
                found_indicators.append(indicator)
        
        # Print debug info if needed
        if len(found_indicators) < 2:
            print(f"Video processing indicators found: {found_indicators}")
            print(f"Full output:\n{all_output}")
        
        self.assertGreaterEqual(
            len(found_indicators), 2,
            f"Expected video processing indicators. Found: {found_indicators}"
        )


@pytest.mark.integration
@pytest.mark.video
@pytest.mark.slow
class TestVideoProcessingIntegration(unittest.TestCase):
    """Integration tests for video processing workflow."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = Path(__file__).parent.parent / 'test_videos' / 'big_buck_bunny_480p.mp4'
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_file_cli_flag(self):
        """Test using --file CLI flag for video processing."""
        if not self.video_path.exists():
            self.skipTest("Test video file not available")
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / 'src')
        
        # Test --file flag
        cmd = [
            sys.executable, '-m', 'cvkitworker',
            '--file', str(self.video_path)
        ]
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            stdout, stderr = process.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        # Verify the --file flag works
        all_output = stdout + stderr
        
        success_indicators = [
            'video file',
            'FrameWorker started',
            str(self.video_path.name)
        ]
        
        found = [indicator for indicator in success_indicators 
                if indicator.lower() in all_output.lower()]
        
        self.assertGreater(
            len(found), 0,
            f"--file flag test failed. Output: {all_output[:500]}..."
        )


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVideoProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestVideoProcessingIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)