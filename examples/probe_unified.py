#!/usr/bin/env python3
"""Example of using UnifiedProbe for both files and webcams."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.utils.probe import UnifiedProbe, VideoInfo, WebcamInfo
from cvkitworker.utils.webcam_probe import WebcamProbe


def probe_source(source):
    """Probe any video source and display info."""
    probe = UnifiedProbe()
    
    try:
        # Convert to int if it's a numeric string (webcam ID)
        if isinstance(source, str) and source.isdigit():
            source = int(source)
        
        # Probe the source
        info = probe.probe(source)
        
        # Display appropriate info based on type
        if isinstance(info, WebcamInfo):
            print(f"\nWebcam Device #{info.device_id}")
            print(f"Resolution: {info.resolution_str}")
            print(f"FPS: {info.fps}")
            print(f"Backend: {info.backend}")
            print(f"FourCC: {info.fourcc}")
            
            if info.brightness is not None:
                print(f"Brightness: {info.brightness}")
            if info.contrast is not None:
                print(f"Contrast: {info.contrast}")
                
        else:  # VideoInfo
            print(f"\nVideo: {info.filename}")
            print(f"Format: {info.format_name}")
            print(f"Duration: {info.duration:.2f} seconds")
            print(f"Size: {info.size / 1024 / 1024:.2f} MB")
            
            # Use unified methods
            width, height = probe.get_resolution(info)
            fps = probe.get_fps(info)
            codec = probe.get_codec(info)
            
            print(f"Resolution: {width}x{height}")
            print(f"FPS: {fps:.2f}")
            print(f"Codec: {codec}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python probe_unified.py <source>")
        print("  <source> can be:")
        print("    - Video file path: /path/to/video.mp4")
        print("    - URL: rtsp://camera.local/stream")
        print("    - Webcam ID: 0, 1, 2...")
        print("\nExamples:")
        print("  python probe_unified.py video.mp4")
        print("  python probe_unified.py 0  # Default webcam")
        print("\nList available webcams:")
        print("  python probe_unified.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        # List available webcams
        webcams = WebcamProbe.list_available_webcams()
        print("\nAvailable webcams:")
        for device_id in sorted(webcams.keys()):
            print(f"  Device {device_id}")
            try:
                info = WebcamProbe.probe(device_id)
                print(f"    Resolution: {info.resolution_str}")
                print(f"    FPS: {info.fps}")
            except Exception as e:
                print(f"    Error: {e}")
    else:
        probe_source(sys.argv[1])


if __name__ == "__main__":
    main()