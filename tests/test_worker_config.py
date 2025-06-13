#!/usr/bin/env python3
"""
Test cases for worker configuration functionality.
"""

import unittest
import os
import json
import tempfile
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.config.parse_config import ConfigParser


class TestWorkerConfiguration(unittest.TestCase):
    """Test worker configuration parsing and priority."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Clear environment variables that might affect tests
        self.original_env = os.environ.get('CVKIT_WORKERS')
        if 'CVKIT_WORKERS' in os.environ:
            del os.environ['CVKIT_WORKERS']
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Restore original environment
        if self.original_env is not None:
            os.environ['CVKIT_WORKERS'] = self.original_env
        elif 'CVKIT_WORKERS' in os.environ:
            del os.environ['CVKIT_WORKERS']
    
    def test_default_worker_count(self):
        """Test default worker count when no configuration is provided."""
        config = {}
        config_path = os.path.join(self.temp_dir, 'default_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        self.assertEqual(parser.get_worker_count(), 2, "Default worker count should be 2")
        
        workers_config = parser.get_workers_config()
        self.assertEqual(workers_config['detect_workers'], 2)
        self.assertEqual(workers_config['frame_workers'], 1)
    
    def test_config_file_worker_count_object(self):
        """Test worker count from config file using object format."""
        config = {
            "workers": {
                "detect_workers": 4,
                "frame_workers": 1
            }
        }
        config_path = os.path.join(self.temp_dir, 'workers_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        self.assertEqual(parser.get_worker_count(), 4, "Should read detect_workers from config")
        
        workers_config = parser.get_workers_config()
        self.assertEqual(workers_config['detect_workers'], 4)
        self.assertEqual(workers_config['frame_workers'], 1)
    
    def test_config_file_worker_count_integer(self):
        """Test worker count from config file using integer format (backward compatibility)."""
        config = {
            "workers": 6
        }
        config_path = os.path.join(self.temp_dir, 'workers_int_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        self.assertEqual(parser.get_worker_count(), 6, "Should read integer workers from config")
        
        workers_config = parser.get_workers_config()
        self.assertEqual(workers_config['detect_workers'], 6)
        self.assertEqual(workers_config['frame_workers'], 1)
    
    def test_environment_variable_worker_count(self):
        """Test worker count from environment variable."""
        os.environ['CVKIT_WORKERS'] = '8'
        
        config = {}
        config_path = os.path.join(self.temp_dir, 'env_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        self.assertEqual(parser.get_worker_count(), 8, "Should read workers from environment variable")
    
    def test_environment_variable_priority_over_config(self):
        """Test that environment variable takes priority over config file."""
        os.environ['CVKIT_WORKERS'] = '5'
        
        config = {
            "workers": {
                "detect_workers": 3
            }
        }
        config_path = os.path.join(self.temp_dir, 'priority_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        self.assertEqual(parser.get_worker_count(), 5, "Environment variable should override config file")
    
    def test_invalid_environment_variable(self):
        """Test handling of invalid environment variable values."""
        os.environ['CVKIT_WORKERS'] = 'invalid'
        
        config = {
            "workers": {
                "detect_workers": 3
            }
        }
        config_path = os.path.join(self.temp_dir, 'invalid_env_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        # Should fall back to config file value when env var is invalid
        self.assertEqual(parser.get_worker_count(), 3, "Should fall back to config when env var is invalid")
    
    def test_negative_worker_count_rejected(self):
        """Test that negative worker counts are rejected."""
        os.environ['CVKIT_WORKERS'] = '-1'
        
        config = {}
        config_path = os.path.join(self.temp_dir, 'negative_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        # Should fall back to default when negative value provided
        self.assertEqual(parser.get_worker_count(), 2, "Should reject negative worker count")
    
    def test_zero_worker_count_rejected(self):
        """Test that zero worker count is rejected."""
        config = {
            "workers": {
                "detect_workers": 0
            }
        }
        config_path = os.path.join(self.temp_dir, 'zero_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        
        # Should fall back to default when zero value provided
        self.assertEqual(parser.get_worker_count(), 2, "Should reject zero worker count")
    
    def test_workers_config_complete(self):
        """Test that get_workers_config returns complete configuration."""
        config = {
            "workers": {
                "detect_workers": 4,
                "custom_setting": "test"
            }
        }
        config_path = os.path.join(self.temp_dir, 'complete_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        workers_config = parser.get_workers_config()
        
        # Should include both default and custom settings
        self.assertEqual(workers_config['detect_workers'], 4)
        self.assertEqual(workers_config['frame_workers'], 1)
        self.assertEqual(workers_config['custom_setting'], "test")
    
    def test_edge_cases(self):
        """Test various edge cases in worker configuration."""
        # Test very large worker count
        config = {"workers": {"detect_workers": 100}}
        config_path = os.path.join(self.temp_dir, 'large_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        self.assertEqual(parser.get_worker_count(), 100, "Should accept large worker counts")
        
        # Test string number in config
        config = {"workers": {"detect_workers": "4"}}
        config_path = os.path.join(self.temp_dir, 'string_config.json')
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        parser = ConfigParser(config_path)
        self.assertEqual(parser.get_worker_count(), 4, "Should convert string numbers")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)