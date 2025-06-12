#!/usr/bin/env python3
"""
Download test videos for testing the cvkitworker file input functionality.
Videos are not stored in git - they are downloaded as needed.
"""

import os
import requests
from pathlib import Path
from loguru import logger
import sys


def download_file(url, filename, target_dir="test_videos"):
    """Download a file from URL to target directory."""
    target_path = Path(target_dir)
    target_path.mkdir(exist_ok=True)
    
    file_path = target_path / filename
    
    # Skip if file already exists
    if file_path.exists():
        logger.info(f"File already exists: {file_path}")
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


def get_test_videos():
    """Download standard test videos for computer vision testing."""
    videos = [
        {
            "name": "sample_faces.mp4",
            "url": "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
            "description": "Sample video for testing (1MB, 720p)"
        },
        {
            "name": "big_buck_bunny_480p.mp4", 
            "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "description": "Big Buck Bunny sample video (480p)"
        }
    ]
    
    downloaded_files = []
    
    for video in videos:
        logger.info(f"Getting {video['description']}")
        file_path = download_file(video["url"], video["name"])
        if file_path:
            downloaded_files.append(file_path)
    
    return downloaded_files


def main():
    """Main function to download test videos."""
    logger.info("Downloading test videos for cvkitworker testing")
    
    # Change to project root if running from scripts directory
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
    
    downloaded = get_test_videos()
    
    if downloaded:
        logger.info(f"Successfully downloaded {len(downloaded)} test videos:")
        for file_path in downloaded:
            logger.info(f"  - {file_path}")
        
        logger.info("\nTo test with downloaded videos:")
        for file_path in downloaded:
            logger.info(f"  cvkitworker --file {file_path}")
    else:
        logger.error("No videos were downloaded successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()