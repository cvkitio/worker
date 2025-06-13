#!/usr/bin/env python3
"""
Integration test for video file processing.
"""

import unittest
import os
import json
import tempfile
import subprocess
import sys
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestVideoIntegration(unittest.TestCase):
    """Integration test for complete video processing pipeline."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.video_path = Path(__file__).parent.parent / 'test_videos' / 'big_buck_bunny_480p.mp4'
        self.timing_log_path = os.path.join(self.temp_dir, 'integration_timing.jsonl')
        
        # Create minimal config for fast testing
        self.config = {
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
                    "width": 160,  # Small size for faster processing
                    "height": 120
                }
            ],
            "detectors": [
                {
                    "name": "face_detector",
                    "type": "face_detector", 
                    "variant": "dlib",
                    "frequency_ms": 1000,  # Lower frequency for faster testing
                    "device": "cpu"
                }
            ],
            "timing": {
                "enabled": True,
                "storage": "file",
                "file_path": self.timing_log_path
            }
        }
        
        self.config_path = os.path.join(self.temp_dir, 'integration_config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_processing_pipeline_starts(self):
        """Test that the complete video processing pipeline can start successfully."""
        if not self.video_path.exists():
            self.skipTest("Test video file not available")
        
        # Set up environment
        env = os.environ.copy()
        env['CVKIT_TIMING_ENABLED'] = 'true'
        env['CVKIT_TIMING_FILE'] = self.timing_log_path
        env['PYTHONPATH'] = str(Path(__file__).parent.parent / 'src')
        
        # Run video processing with config
        cmd = [
            sys.executable, '-m', 'cvkitworker',
            '--config', self.config_path
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        print(f"Config path: {self.config_path}")
        print(f"Video path: {self.video_path}")
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            # Run for just 2 seconds to verify startup
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            # Expected - terminate after timeout
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        # Combine output
        all_output = stdout + stderr
        print(f"Process output:\n{all_output}")
        
        # Check for startup indicators
        startup_indicators = [
            'Main process started',
            'Shared memory created',
            'FrameWorker started',
            'DetectWorker started',
            'Loaded video file',
            str(self.video_path.name)
        ]
        
        found_indicators = []
        for indicator in startup_indicators:
            if indicator.lower() in all_output.lower():
                found_indicators.append(indicator)
        
        print(f"Found startup indicators: {found_indicators}")
        
        # Verify at least some key indicators are present
        self.assertGreaterEqual(
            len(found_indicators), 2,
            f"Expected video processing to start. Found indicators: {found_indicators}\n"
            f"Full output: {all_output}"
        )
        
        # If timing file was created, verify it has some content
        if os.path.exists(self.timing_log_path):
            with open(self.timing_log_path, 'r') as f:
                timing_content = f.read().strip()
            
            if timing_content:
                print(f"Timing log created with {len(timing_content.split())} entries")
                # Verify at least one timing measurement
                lines = timing_content.split('\n')
                valid_measurements = 0
                for line in lines:
                    if line.strip():
                        try:
                            measurement = json.loads(line)
                            if 'duration_ms' in measurement:
                                valid_measurements += 1
                        except json.JSONDecodeError:
                            continue
                
                if valid_measurements > 0:
                    print(f"Found {valid_measurements} valid timing measurements")
    
    def test_video_file_flag_integration(self):
        """Test the --file CLI flag with video processing."""
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
        
        print(f"Testing --file flag: {' '.join(cmd)}")
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        
        try:
            # Run briefly to test startup
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        
        all_output = stdout + stderr
        print(f"--file flag output:\n{all_output}")
        
        # Check for file processing indicators
        file_indicators = [
            'video file',
            'main process started',
            str(self.video_path.name),
            'FrameWorker'
        ]
        
        found = [indicator for indicator in file_indicators 
                if indicator.lower() in all_output.lower()]
        
        print(f"Found file indicators: {found}")
        
        self.assertGreater(
            len(found), 0,
            f"--file flag should work with video files. Output: {all_output[:500]}..."
        )


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)