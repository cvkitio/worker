#!/usr/bin/env python3
"""
Download Kaggle human faces dataset for face detection testing.

This script downloads the human faces dataset from Kaggle and prepares
individual face images for testing.
"""

import os
import cv2
import shutil
from pathlib import Path
from loguru import logger
import kagglehub


def setup_kaggle_auth():
    """Check and setup Kaggle authentication."""
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    
    if not kaggle_json.exists():
        logger.error("Kaggle API credentials not found!")
        print("\n🔑 Kaggle Authentication Required:")
        print("1. Go to https://www.kaggle.com/account")
        print("2. Click 'Create New API Token'")
        print("3. Download kaggle.json file")
        print("4. Move it to ~/.kaggle/kaggle.json")
        print("5. Run: chmod 600 ~/.kaggle/kaggle.json")
        print("\nAlternatively, set environment variables:")
        print("export KAGGLE_USERNAME=your_username")
        print("export KAGGLE_KEY=your_api_key")
        return False
    
    # Set proper permissions
    kaggle_json.chmod(0o600)
    logger.info("Kaggle credentials found and configured")
    return True


def download_kaggle_dataset():
    """Download the human faces dataset from Kaggle."""
    logger.info("Downloading human faces dataset from Kaggle...")
    
    try:
        # Download the dataset
        path = kagglehub.dataset_download("sbaghbidi/human-faces-object-detection")
        logger.info(f"Dataset downloaded to: {path}")
        return Path(path)
        
    except Exception as e:
        logger.error(f"Failed to download Kaggle dataset: {e}")
        
        # Check for common issues
        if "403" in str(e) or "Unauthorized" in str(e):
            logger.error("Authentication failed. Please check your Kaggle credentials.")
        elif "404" in str(e):
            logger.error("Dataset not found. Please check the dataset name.")
        elif "ConnectionError" in str(e):
            logger.error("Network connection failed. Please check your internet connection.")
        
        return None


def extract_face_images(dataset_path, output_dir, max_faces=10):
    """Extract face images from the downloaded dataset."""
    faces_dir = output_dir / "faces"
    faces_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Extracting face images from {dataset_path}")
    
    # Find image files in the dataset
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(dataset_path.rglob(f"*{ext}"))
        image_files.extend(dataset_path.rglob(f"*{ext.upper()}"))
    
    logger.info(f"Found {len(image_files)} potential image files")
    
    extracted_faces = []
    
    for i, img_path in enumerate(image_files[:max_faces * 3]):  # Try more files in case some are invalid
        if len(extracted_faces) >= max_faces:
            break
            
        try:
            # Load and verify image
            img = cv2.imread(str(img_path))
            if img is None:
                logger.warning(f"Could not load image: {img_path}")
                continue
            
            # Check if image is reasonable size
            height, width = img.shape[:2]
            if height < 50 or width < 50:
                logger.warning(f"Image too small: {img_path} ({width}x{height})")
                continue
            
            # Resize to standard size for consistency (max 400px)
            max_size = 400
            if height > max_size or width > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height))
            
            # Save extracted face
            face_filename = f"face_{len(extracted_faces) + 1:03d}.jpg"
            face_path = faces_dir / face_filename
            
            success = cv2.imwrite(str(face_path), img)
            if success:
                extracted_faces.append(face_path)
                logger.info(f"Extracted face {len(extracted_faces)}: {face_filename} ({img.shape[1]}x{img.shape[0]})")
            else:
                logger.warning(f"Failed to save image: {face_filename}")
                
        except Exception as e:
            logger.warning(f"Error processing {img_path}: {e}")
            continue
    
    logger.info(f"Successfully extracted {len(extracted_faces)} face images")
    return extracted_faces


def create_summary(faces_dir, extracted_faces):
    """Create a summary file of downloaded faces."""
    summary_path = faces_dir.parent / "faces_summary.txt"
    
    with open(summary_path, 'w') as f:
        f.write("Kaggle Human Faces Dataset Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total faces extracted: {len(extracted_faces)}\n")
        f.write(f"Storage location: {faces_dir}\n\n")
        
        f.write("Face files:\n")
        for i, face_path in enumerate(extracted_faces, 1):
            # Get image dimensions
            img = cv2.imread(str(face_path))
            if img is not None:
                height, width = img.shape[:2]
                file_size = face_path.stat().st_size / 1024  # KB
                f.write(f"  {i:2d}. {face_path.name} - {width}x{height} ({file_size:.1f} KB)\n")
    
    logger.info(f"Summary saved to: {summary_path}")
    return summary_path


def main():
    """Main function to download Kaggle faces dataset."""
    logger.info("Starting Kaggle faces dataset download")
    
    # Setup output directory
    output_dir = Path("kaggle_faces")
    output_dir.mkdir(exist_ok=True)
    
    # Add to .gitignore
    gitignore_path = Path(".gitignore")
    gitignore_content = ""
    
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
    
    if "kaggle_faces/" not in gitignore_content:
        with open(gitignore_path, "a") as f:
            f.write("\n# Kaggle faces dataset (excluded from git)\nkaggle_faces/\n")
        logger.info("Added kaggle_faces/ to .gitignore")
    
    # Check Kaggle authentication
    if not setup_kaggle_auth():
        return False
    
    # Download dataset
    dataset_path = download_kaggle_dataset()
    if not dataset_path:
        return False
    
    # Extract face images
    extracted_faces = extract_face_images(dataset_path, output_dir)
    
    if not extracted_faces:
        logger.error("No face images were extracted")
        return False
    
    # Create summary
    summary_path = create_summary(output_dir / "faces", extracted_faces)
    
    # Success message
    logger.info("Kaggle faces dataset download completed successfully!")
    
    print(f"\n✅ Download Complete!")
    print(f"📁 Location: {output_dir}")
    print(f"🖼️  Faces extracted: {len(extracted_faces)}")
    print(f"📄 Summary: {summary_path}")
    
    print(f"\n🚀 Next steps:")
    print(f"1. Review face images in: {output_dir / 'faces'}")
    print(f"2. Create test video: python create_kaggle_test_dataset.py")
    print(f"3. Run tests: python test_kaggle_face_detection.py")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)