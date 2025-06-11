#!/usr/bin/env python3
"""
Create a controlled test dataset using Kaggle human faces dataset.

This script downloads face images from Kaggle, creates blank frames, and uses
ffmpeg to generate a test video with known face/no-face frame locations.
"""

import os
import json
import cv2
import numpy as np
import subprocess
from pathlib import Path
from loguru import logger
import kagglehub


def create_test_dir():
    """Create test directory and ensure it's excluded from git."""
    test_dir = Path("test_data_kaggle")
    test_dir.mkdir(exist_ok=True)
    
    # Add to .gitignore
    gitignore_path = Path(".gitignore")
    gitignore_content = ""
    
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
    
    if "test_data_kaggle/" not in gitignore_content:
        with open(gitignore_path, "a") as f:
            f.write("\n# Kaggle test data (excluded from git)\ntest_data_kaggle/\n")
        logger.info("Added test_data_kaggle/ to .gitignore")
    
    return test_dir


def download_kaggle_faces(test_dir):
    """Download human faces dataset from Kaggle."""
    logger.info("Downloading human faces dataset from Kaggle...")
    
    try:
        # Download the dataset
        path = kagglehub.dataset_download("sbaghbidi/human-faces-object-detection")
        logger.info(f"Dataset downloaded to: {path}")
        
        # Find image files in the downloaded dataset
        dataset_path = Path(path)
        image_files = []
        
        # Look for common image extensions
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            image_files.extend(dataset_path.glob(f"**/{ext}"))
            image_files.extend(dataset_path.glob(f"**/{ext.upper()}"))
        
        logger.info(f"Found {len(image_files)} images in dataset")
        
        # Copy first few images to our test directory
        faces_dir = test_dir / "faces"
        faces_dir.mkdir(exist_ok=True)
        
        selected_faces = []
        max_faces = 5  # Use 5 face images for testing
        
        for i, img_path in enumerate(image_files[:max_faces]):
            # Load and verify image
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            # Resize to standard size for consistency
            img_resized = cv2.resize(img, (300, 300))
            
            # Save to our test directory
            face_filename = f"kaggle_face_{i+1}.jpg"
            face_path = faces_dir / face_filename
            cv2.imwrite(str(face_path), img_resized)
            
            selected_faces.append(face_path)
            logger.info(f"Processed face image: {face_filename} ({img_resized.shape})")
        
        return selected_faces
        
    except Exception as e:
        logger.error(f"Failed to download Kaggle dataset: {e}")
        return []


def create_blank_frames(test_dir, num_blank_frames=3):
    """Create blank frames without faces."""
    blanks_dir = test_dir / "blanks"
    blanks_dir.mkdir(exist_ok=True)
    
    blank_frames = []
    
    for i in range(num_blank_frames):
        # Create different types of blank frames
        if i == 0:
            # Pure black frame
            blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
        elif i == 1:
            # Gray frame
            blank_img = np.full((300, 300, 3), 128, dtype=np.uint8)
        else:
            # Random noise frame (no face patterns)
            blank_img = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
        
        # Add text to identify blank frames
        cv2.putText(blank_img, f"No Face {i+1}", (50, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        blank_filename = f"blank_{i+1}.jpg"
        blank_path = blanks_dir / blank_filename
        cv2.imwrite(str(blank_path), blank_img)
        
        blank_frames.append(blank_path)
        logger.info(f"Created blank frame: {blank_filename}")
    
    return blank_frames


def create_frame_sequence(face_images, blank_frames, test_dir):
    """Create a sequence of frames for video generation."""
    frames_dir = test_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # Create frame sequence: face, face, blank, face, blank, blank, face
    frame_sequence = []
    frame_metadata = {
        "fps": 1,  # 1 frame per second for easy testing
        "frame_size": [300, 300],
        "frames": []
    }
    
    # Define the sequence pattern
    sequence_plan = [
        ("face", 0),    # Frame 0: Face 1
        ("face", 1),    # Frame 1: Face 2  
        ("blank", 0),   # Frame 2: Blank 1
        ("face", 2),    # Frame 3: Face 3
        ("blank", 1),   # Frame 4: Blank 2
        ("blank", 2),   # Frame 5: Blank 3
        ("face", 3),    # Frame 6: Face 4 (if available)
        ("face", 4),    # Frame 7: Face 5 (if available)
    ]
    
    frame_number = 0
    
    for frame_type, index in sequence_plan:
        if frame_type == "face" and index < len(face_images):
            source_path = face_images[index]
            has_face = True
            source_type = "face"
        elif frame_type == "blank" and index < len(blank_frames):
            source_path = blank_frames[index]
            has_face = False
            source_type = "blank"
        else:
            # Skip if we don't have enough images
            continue
        
        # Copy image to frames directory with sequential naming
        frame_filename = f"frame_{frame_number:04d}.jpg"
        frame_path = frames_dir / frame_filename
        
        # Load, ensure consistent size, and save
        img = cv2.imread(str(source_path))
        img_resized = cv2.resize(img, (300, 300))
        
        # Add frame number overlay
        cv2.putText(img_resized, f"Frame {frame_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        cv2.imwrite(str(frame_path), img_resized)
        
        # Record metadata
        frame_info = {
            "frame_number": frame_number,
            "filename": frame_filename,
            "has_face": has_face,
            "source_type": source_type,
            "source_file": source_path.name
        }
        
        frame_metadata["frames"].append(frame_info)
        frame_sequence.append(frame_path)
        
        logger.info(f"Frame {frame_number}: {source_type} ({'face' if has_face else 'no face'})")
        frame_number += 1
    
    return frame_sequence, frame_metadata


def create_video_with_ffmpeg(frames_dir, test_dir, metadata):
    """Use ffmpeg to create video from frame sequence."""
    video_path = test_dir / "test_faces_kaggle.mp4"
    
    # ffmpeg command to create video from images
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-framerate", "1",  # 1 fps
        "-i", str(frames_dir / "frame_%04d.jpg"),  # Input pattern
        "-c:v", "libx264",  # Video codec
        "-pix_fmt", "yuv420p",  # Pixel format for compatibility
        "-r", "1",  # Output framerate
        str(video_path)
    ]
    
    logger.info(f"Creating video with ffmpeg: {' '.join(ffmpeg_cmd)}")
    
    try:
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
        logger.info(f"Video created successfully: {video_path}")
        return video_path
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg failed: {e}")
        logger.error(f"ffmpeg stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg.")
        return None


def main():
    """Main function to create Kaggle-based test dataset."""
    logger.info("Creating face detection test dataset using Kaggle data")
    
    # Create test directory
    test_dir = create_test_dir()
    
    # Download face images from Kaggle
    face_images = download_kaggle_faces(test_dir)
    
    if not face_images:
        logger.error("No face images downloaded. Cannot create test video.")
        return
    
    # Create blank frames
    blank_frames = create_blank_frames(test_dir)
    
    # Create frame sequence
    frame_sequence, metadata = create_frame_sequence(face_images, blank_frames, test_dir)
    
    # Save metadata
    metadata_path = test_dir / "test_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {metadata_path}")
    
    # Create video with ffmpeg
    video_path = create_video_with_ffmpeg(test_dir / "frames", test_dir, metadata)
    
    if video_path and video_path.exists():
        logger.info("Test dataset created successfully!")
        print(f"\nTest video: {video_path}")
        print(f"Metadata: {metadata_path}")
        print(f"Total frames: {len(metadata['frames'])}")
        
        # Print frame summary
        print(f"\nFrame summary:")
        for frame_info in metadata['frames']:
            face_status = "HAS FACE" if frame_info['has_face'] else "NO FACE"
            print(f"  Frame {frame_info['frame_number']}: {face_status} ({frame_info['source_type']})")
        
        print(f"\nUsage:")
        print(f"  python -m cvkitio_worker.main --video {video_path}")
        print(f"  python test_kaggle_face_detection.py")
    else:
        logger.error("Failed to create test dataset")


if __name__ == "__main__":
    main()