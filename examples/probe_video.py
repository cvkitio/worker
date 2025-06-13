#!/usr/bin/env python3
"""Example of using FFProbe to extract video metadata."""
# TODO don't really want these files in the examples dir

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cvkitworker.utils.probe import FFProbe


def main():
    """Demonstrate FFProbe usage."""
    if len(sys.argv) < 2:
        print("Usage: python probe_video.py <video_file_or_url>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    try:
        # Create probe instance
        probe = FFProbe()
        
        # Extract metadata
        info = probe.probe(video_path)
        
        # Display general info
        print(f"\nVideo: {info.filename}")
        print(f"Format: {info.format_name} ({info.format_long_name})")
        print(f"Duration: {info.duration:.2f} seconds")
        print(f"Size: {info.size / 1024 / 1024:.2f} MB")
        print(f"Overall bitrate: {info.bit_rate / 1000:.0f} kbps")
        print(f"Number of streams: {info.nb_streams}")
        
        # Display video stream info
        video_stream = probe.get_primary_video_stream(info)
        if video_stream:
            print(f"\nVideo Stream #{video_stream.index}:")
            print(f"  Codec: {video_stream.codec_name} ({video_stream.codec_long_name})")
            print(f"  Resolution: {video_stream.width}x{video_stream.height}")
            print(f"  Frame rate: {video_stream.fps:.2f} fps")
            print(f"  Pixel format: {video_stream.pix_fmt}")
            if video_stream.bit_rate:
                print(f"  Bitrate: {video_stream.bit_rate / 1000:.0f} kbps")
        
        # Display audio stream info
        audio_stream = probe.get_primary_audio_stream(info)
        if audio_stream:
            print(f"\nAudio Stream #{audio_stream.index}:")
            print(f"  Codec: {audio_stream.codec_name} ({audio_stream.codec_long_name})")
            print(f"  Sample rate: {audio_stream.sample_rate} Hz")
            print(f"  Channels: {audio_stream.channels}")
            if audio_stream.channel_layout:
                print(f"  Channel layout: {audio_stream.channel_layout}")
            if audio_stream.bit_rate:
                print(f"  Bitrate: {audio_stream.bit_rate / 1000:.0f} kbps")
        
        # Display all streams summary
        print(f"\nAll streams:")
        for stream in info.streams:
            print(f"  [{stream.index}] {stream.codec_type}: {stream.codec_name}")
            
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()