import json
import os
from pathlib import Path


class ConfigParser:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}
        self.parse_config()

    def parse_config(self):
        """Parse configuration file (supports JSON and YAML)."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        file_path = Path(self.config_file)
        
        try:
            with open(self.config_file, 'r') as file:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    # Try to import yaml, fall back to JSON if not available
                    try:
                        import yaml
                        self.config = yaml.safe_load(file)
                        print(f"Loaded YAML configuration from {self.config_file}")
                    except ImportError:
                        print("Warning: PyYAML not installed. Please install with: pip install PyYAML")
                        print("Falling back to JSON parsing...")
                        file.seek(0)
                        self.config = json.load(file)
                else:
                    self.config = json.load(file)
                    print(f"Loaded JSON configuration from {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {self.config_file}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse config file {self.config_file}: {e}")
        
        # Validate that config is not empty
        if not self.config:
            raise ValueError(f"Configuration file {self.config_file} is empty or invalid")

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
