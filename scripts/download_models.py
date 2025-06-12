#!/usr/bin/env python3
"""
Download face detection models for cvkitworker.
Models are downloaded to models/ directory and not stored in git.
"""

import os
import requests
import kagglehub
from pathlib import Path
from loguru import logger
import sys
import gzip
import tarfile
import zipfile


def ensure_models_dir():
    """Ensure models directory exists."""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    return models_dir


def download_file(url, filename, target_dir="models"):
    """Download a file from URL to target directory."""
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    file_path = target_path / filename
    
    # Skip if file already exists
    if file_path.exists():
        logger.info(f"Model already exists: {file_path}")
        return str(file_path)
    
    logger.info(f"Downloading {filename} from {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}%", end="", flush=True)
        
        print()  # New line after progress
        logger.info(f"Downloaded: {file_path} ({downloaded} bytes)")
        return str(file_path)
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        if file_path.exists():
            file_path.unlink()  # Remove partial file
        return None


def download_dlib_models():
    """Download dlib face detection models."""
    models_dir = ensure_models_dir()
    downloaded = []
    
    # 1. Shape predictor for facial landmarks
    shape_predictor_url = "https://github.com/italojs/facial-landmarks-recognition/raw/master/shape_predictor_68_face_landmarks.dat"
    shape_predictor_path = download_file(
        shape_predictor_url,
        "shape_predictor_68_face_landmarks.dat"
    )
    if shape_predictor_path:
        downloaded.append(shape_predictor_path)
    
    # 2. Try to download CNN face detection model from alternative source
    cnn_model_url = "https://github.com/davisking/dlib-models/raw/master/mmod_human_face_detector.dat.bz2"
    try:
        logger.info("Downloading CNN face detection model...")
        response = requests.get(cnn_model_url, stream=True)
        response.raise_for_status()
        
        compressed_path = models_dir / "mmod_human_face_detector.dat.bz2"
        final_path = models_dir / "mmod_human_face_detector.dat"
        
        # Download compressed file
        with open(compressed_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Decompress
        import bz2
        with bz2.BZ2File(compressed_path, 'rb') as f_in:
            with open(final_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        # Remove compressed file
        compressed_path.unlink()
        
        logger.info(f"Downloaded and decompressed: {final_path}")
        downloaded.append(str(final_path))
        
    except Exception as e:
        logger.warning(f"Failed to download CNN model from GitHub: {e}")
        
        # Try Kaggle as backup
        try:
            logger.info("Trying to download from Kaggle...")
            path = kagglehub.dataset_download("leeast/mmod-human-face-detector-dat")
            
            # Find the .dat file in the downloaded directory
            dat_files = list(Path(path).glob("*.dat"))
            if dat_files:
                source_file = dat_files[0]
                target_file = models_dir / "mmod_human_face_detector.dat"
                
                # Copy the file to our models directory
                import shutil
                shutil.copy2(source_file, target_file)
                
                logger.info(f"Downloaded from Kaggle: {target_file}")
                downloaded.append(str(target_file))
            else:
                logger.error("No .dat file found in Kaggle download")
                
        except Exception as kaggle_error:
            logger.error(f"Failed to download from Kaggle: {kaggle_error}")
    
    return downloaded


def download_opencv_models():
    """Download OpenCV face detection models."""
    models_dir = ensure_models_dir()
    downloaded = []
    
    # OpenCV DNN face detection models
    models = [
        {
            "name": "opencv_face_detector_uint8.pb",
            "url": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/opencv_face_detector_uint8.pb",
            "description": "OpenCV DNN face detector (protobuf)"
        },
        {
            "name": "opencv_face_detector.pbtxt",
            "url": "https://github.com/opencv/opencv/raw/master/samples/dnn/face_detector/opencv_face_detector.pbtxt",
            "description": "OpenCV DNN face detector config"
        }
    ]
    
    for model in models:
        logger.info(f"Downloading {model['description']}")
        file_path = download_file(model["url"], model["name"])
        if file_path:
            downloaded.append(file_path)
    
    return downloaded


def download_yunet_model():
    """Download YuNet face detection model."""
    models_dir = ensure_models_dir()
    
    yunet_url = "https://github.com/opencv/opencv_zoo/raw/master/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    
    logger.info("Downloading YuNet face detection model")
    file_path = download_file(yunet_url, "face_detection_yunet_2023mar.onnx")
    
    return [file_path] if file_path else []


def create_model_info():
    """Create a models/README.md with information about downloaded models."""
    models_dir = ensure_models_dir()
    readme_path = models_dir / "README.md"
    
    content = """# Face Detection Models

This directory contains face detection models downloaded by cvkitworker.

## Available Models

### dlib Models
- `mmod_human_face_detector.dat` - CNN-based face detector, high accuracy
- `shape_predictor_68_face_landmarks.dat` - 68-point facial landmark predictor

### OpenCV Models
- `opencv_face_detector_uint8.pb` - DNN face detector (protobuf)
- `opencv_face_detector.pbtxt` - DNN face detector configuration
- `face_detection_yunet_2023mar.onnx` - YuNet face detector (ONNX format)

## Usage

Models are automatically downloaded when needed. To manually download:

```bash
python scripts/download_models.py
```

## Model Sources

- dlib models: https://github.com/davisking/dlib-models
- OpenCV models: https://github.com/opencv/opencv_zoo
- YuNet: https://github.com/opencv/opencv_zoo/tree/master/models/face_detection_yunet

Models are not stored in git repository to keep repo size manageable.
"""
    
    with open(readme_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Created model documentation: {readme_path}")


def main():
    """Main function to download all face detection models."""
    logger.info("Downloading face detection models for cvkitworker")
    
    # Change to project root if running from scripts directory
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
    
    all_downloaded = []
    
    logger.info("=== Downloading dlib models ===")
    dlib_models = download_dlib_models()
    all_downloaded.extend(dlib_models)
    
    logger.info("=== Downloading OpenCV models ===")
    opencv_models = download_opencv_models()
    all_downloaded.extend(opencv_models)
    
    logger.info("=== Downloading YuNet model ===")
    yunet_models = download_yunet_model()
    all_downloaded.extend(yunet_models)
    
    # Create documentation
    create_model_info()
    
    if all_downloaded:
        logger.info(f"Successfully downloaded {len(all_downloaded)} models:")
        for model_path in all_downloaded:
            if model_path:  # Check for None values
                model_size = os.path.getsize(model_path) / (1024 * 1024)  # Size in MB
                logger.info(f"  - {model_path} ({model_size:.1f} MB)")
        
        logger.info("\nModels ready for use with cvkitworker!")
        logger.info("Example usage:")
        logger.info("  cvkitworker --file test_video.mp4")
        
    else:
        logger.error("No models were downloaded successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()