#!/usr/bin/env python3
"""
Download test videos with faces for face detection testing.

This script downloads sample videos from public sources and stores them in a 
test_videos/ directory that is excluded from git tracking.
"""

import os
import requests
import sys
from pathlib import Path
from loguru import logger

def create_test_videos_dir():
    """Create test_videos directory if it doesn't exist."""
    test_dir = Path("test_videos")
    test_dir.mkdir(exist_ok=True)
    
    # Create .gitignore entry to exclude test videos
    gitignore_path = Path(".gitignore")
    gitignore_content = ""
    
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
    
    if "test_videos/" not in gitignore_content:
        with open(gitignore_path, "a") as f:
            f.write("\n# Test videos (excluded from git)\ntest_videos/\n")
        logger.info("Added test_videos/ to .gitignore")
    
    return test_dir

def download_file(url, filename, test_dir):
    """Download a file from URL to the test directory."""
    file_path = test_dir / filename
    
    if file_path.exists():
        logger.info(f"File already exists: {filename}")
        return file_path
    
    logger.info(f"Downloading {filename} from {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded: {filename} ({file_path.stat().st_size} bytes)")
        return file_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        return None

def main():
    """Main function to download test videos."""
    logger.info("Starting test video download")
    
    # Create test videos directory
    test_dir = create_test_videos_dir()
    
    # Test videos with faces from various sources
    test_videos = [
        {
            "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "filename": "sample_720p.mp4",
            "description": "Sample 720p video"
        },
        {
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "filename": "big_buck_bunny.mp4", 
            "description": "Big Buck Bunny (animation with character faces)"
        },
        {
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "filename": "elephants_dream.mp4",
            "description": "Elephants Dream (animation with character faces)"
        }
    ]
    
    downloaded_files = []
    
    for video in test_videos:
        logger.info(f"Processing: {video['description']}")
        file_path = download_file(video["url"], video["filename"], test_dir)
        if file_path:
            downloaded_files.append(file_path)
    
    # Create a simple README for the test videos
    readme_path = test_dir / "README.md"
    readme_content = """# Test Videos

This directory contains test videos for face detection testing.

## Downloaded Videos:
"""
    
    for i, video in enumerate(test_videos):
        if i < len(downloaded_files):
            readme_content += f"- **{video['filename']}**: {video['description']}\n"
    
    readme_content += """
## Usage:

Run face detection on a test video:
```bash
python -m cvkitio_worker.main --video test_videos/sample_720p.mp4
```

## Note:
These files are excluded from git tracking via .gitignore.
"""
    
    readme_path.write_text(readme_content)
    
    logger.info(f"Downloaded {len(downloaded_files)} test videos to {test_dir}")
    logger.info("Test videos are ready for face detection testing!")
    
    # Show usage examples
    print("\nUsage examples:")
    for file_path in downloaded_files:
        print(f"  python -m cvkitio_worker.main --video {file_path}")

if __name__ == "__main__":
    main()