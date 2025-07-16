import json
import os


class ConfigParser:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}
        self.parse_config()

    def parse_config(self):
        with open(self.config_file, 'r') as file:
            self.config = json.load(file)

    def get_config(self):
        return self.config

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value

    def remove(self, key):
        if key in self.config:
            del self.config[key]

    def has(self, key):
        return key in self.config
    
    def get_worker_count(self):
        """Get the number of detect workers to spawn.
        
        Priority order:
        1. Environment variable CVKIT_WORKERS
        2. Config file workers.detect_workers
        3. Config file workers (for backward compatibility)
        4. Default: 2
        """
        # Check environment variable first
        env_workers = os.getenv('CVKIT_WORKERS')
        if env_workers:
            try:
                workers = int(env_workers)
                if workers > 0:
                    return workers
            except ValueError:
                pass
        
        # Check config file
        workers_config = self.get('workers', {})
        if isinstance(workers_config, dict):
            # New format: workers.detect_workers
            detect_workers = workers_config.get('detect_workers')
            if detect_workers is not None:
                try:
                    workers = int(detect_workers)
                    if workers > 0:
                        return workers
                except (ValueError, TypeError):
                    pass
        elif isinstance(workers_config, int):
            # Backward compatibility: workers as integer
            if workers_config > 0:
                return workers_config
        
        # Default
        return 2
    
    def get_workers_config(self):
        """Get complete workers configuration with defaults."""
        default_config = {
            'detect_workers': self.get_worker_count(),
            'frame_workers': 1  # Always 1 frame worker (producer)
        }
        
        workers_config = self.get('workers', {})
        if isinstance(workers_config, dict):
            # Merge with defaults
            result = default_config.copy()
            result.update(workers_config)
            return result
        elif isinstance(workers_config, int):
            # Backward compatibility
            result = default_config.copy()
            result['detect_workers'] = workers_config
            return result
        
        return default_config
