import os
import json
import tempfile


def create_file_config(file_path):
    """Create temporary configuration for file input."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    
    config = {
        "receivers": [
            {
                "name": "file_input",
                "type": "file",
                "source": file_path
            }
        ],
        "detectors": [
            {
                "name": "face_detector",
                "type": "face_detector",
                "variant": "dlib",
                "frequency_ms": 500,
                "scale": 1.0,
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        return f.name


def create_webcam_config():
    """Create temporary configuration for webcam input."""
    config = {
        "receivers": [
            {
                "name": "webcam_input",
                "type": "webcam",
                "source": 0
            }
        ],
        "detectors": [
            {
                "name": "face_detector",
                "type": "face_detector",
                "variant": "dlib",
                "frequency_ms": 500,
                "scale": 1.0,
                "device": "cpu"
            }
        ],
        "preprocessors": [
            {
                "type": "resize",
                "width": 640
            }
        ]
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        return f.name