import json


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