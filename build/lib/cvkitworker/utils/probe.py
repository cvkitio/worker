import json
import subprocess
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from loguru import logger
from .webcam_probe import WebcamProbe, WebcamInfo


@dataclass
class StreamInfo:
    """Information about a single stream in a video file."""
    index: int
    codec_name: str
    codec_type: str  # video, audio, subtitle
    codec_long_name: str
    profile: Optional[str] = None
    
    # Video-specific
    width: Optional[int] = None
    height: Optional[int] = None
    coded_width: Optional[int] = None
    coded_height: Optional[int] = None
    display_aspect_ratio: Optional[str] = None
    pix_fmt: Optional[str] = None
    fps: Optional[float] = None
    avg_frame_rate: Optional[str] = None
    time_base: Optional[str] = None
    
    # Audio-specific
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    channel_layout: Optional[str] = None
    
    # Common
    bit_rate: Optional[int] = None
    duration: Optional[float] = None
    nb_frames: Optional[int] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class VideoInfo:
    """Complete video file information."""
    filename: str
    format_name: str
    format_long_name: str
    duration: float
    size: int
    bit_rate: int
    nb_streams: int
    streams: List[StreamInfo]
    format_tags: Optional[Dict[str, str]] = None


class FFProbe:
    """Utility class to extract video metadata using ffprobe."""
    
    def __init__(self, ffprobe_path: str = "ffprobe"):
        """
        Initialize FFProbe with optional custom path.
        
        Args:
            ffprobe_path: Path to ffprobe executable (default: "ffprobe")
        """
        self.ffprobe_path = ffprobe_path
        self._verify_ffprobe()
    
    def _verify_ffprobe(self) -> None:
        """Verify ffprobe is available."""
        try:
            subprocess.run(
                [self.ffprobe_path, "-version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"ffprobe not found or not working: {e}")
    
    def probe(self, video_path: str) -> VideoInfo:
        """
        Extract metadata from video file.
        
        Args:
            video_path: Path to video file (local file or URL)
            
        Returns:
            VideoInfo object containing all metadata
            
        Raises:
            RuntimeError: If ffprobe fails or video cannot be read
        """
        cmd = [
            self.ffprobe_path,
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-timeout", "5000000",  # 5 second timeout in microseconds
            video_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe failed: {e.stderr}")
            raise RuntimeError(f"Failed to probe video: {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse ffprobe output: {e}")
        
        return self._parse_ffprobe_output(data, video_path)
    
    def _parse_ffprobe_output(self, data: Dict[str, Any], filename: str) -> VideoInfo:
        """Parse ffprobe JSON output into VideoInfo structure."""
        format_info = data.get("format", {})
        streams_data = data.get("streams", [])
        
        # Parse streams
        streams = []
        for stream_data in streams_data:
            stream = self._parse_stream(stream_data)
            streams.append(stream)
        
        # Create VideoInfo
        return VideoInfo(
            filename=filename,
            format_name=format_info.get("format_name", ""),
            format_long_name=format_info.get("format_long_name", ""),
            duration=float(format_info.get("duration", 0)),
            size=int(format_info.get("size", 0)),
            bit_rate=int(format_info.get("bit_rate", 0)),
            nb_streams=int(format_info.get("nb_streams", 0)),
            streams=streams,
            format_tags=format_info.get("tags", {})
        )
    
    def _parse_stream(self, stream_data: Dict[str, Any]) -> StreamInfo:
        """Parse individual stream data."""
        stream = StreamInfo(
            index=int(stream_data.get("index", 0)),
            codec_name=stream_data.get("codec_name", ""),
            codec_type=stream_data.get("codec_type", ""),
            codec_long_name=stream_data.get("codec_long_name", ""),
            profile=stream_data.get("profile"),
            bit_rate=int(stream_data.get("bit_rate", 0)) if stream_data.get("bit_rate") else None,
            duration=float(stream_data.get("duration", 0)) if stream_data.get("duration") else None,
            nb_frames=int(stream_data.get("nb_frames", 0)) if stream_data.get("nb_frames") else None,
            tags=stream_data.get("tags", {})
        )
        
        # Video-specific fields
        if stream.codec_type == "video":
            stream.width = int(stream_data.get("width", 0)) if stream_data.get("width") else None
            stream.height = int(stream_data.get("height", 0)) if stream_data.get("height") else None
            stream.coded_width = int(stream_data.get("coded_width", 0)) if stream_data.get("coded_width") else None
            stream.coded_height = int(stream_data.get("coded_height", 0)) if stream_data.get("coded_height") else None
            stream.display_aspect_ratio = stream_data.get("display_aspect_ratio")
            stream.pix_fmt = stream_data.get("pix_fmt")
            stream.avg_frame_rate = stream_data.get("avg_frame_rate")
            stream.time_base = stream_data.get("time_base")
            
            # Calculate FPS from avg_frame_rate
            if stream.avg_frame_rate:
                try:
                    num, den = map(int, stream.avg_frame_rate.split('/'))
                    stream.fps = num / den if den != 0 else None
                except (ValueError, ZeroDivisionError):
                    stream.fps = None
        
        # Audio-specific fields
        elif stream.codec_type == "audio":
            stream.sample_rate = int(stream_data.get("sample_rate", 0)) if stream_data.get("sample_rate") else None
            stream.channels = int(stream_data.get("channels", 0)) if stream_data.get("channels") else None
            stream.channel_layout = stream_data.get("channel_layout")
        
        return stream
    
    def get_video_streams(self, video_info: VideoInfo) -> List[StreamInfo]:
        """Get all video streams from VideoInfo."""
        return [s for s in video_info.streams if s.codec_type == "video"]
    
    def get_audio_streams(self, video_info: VideoInfo) -> List[StreamInfo]:
        """Get all audio streams from VideoInfo."""
        return [s for s in video_info.streams if s.codec_type == "audio"]
    
    def get_primary_video_stream(self, video_info: VideoInfo) -> Optional[StreamInfo]:
        """Get the primary (first) video stream."""
        video_streams = self.get_video_streams(video_info)
        return video_streams[0] if video_streams else None
    
    def get_primary_audio_stream(self, video_info: VideoInfo) -> Optional[StreamInfo]:
        """Get the primary (first) audio stream."""
        audio_streams = self.get_audio_streams(video_info)
        return audio_streams[0] if audio_streams else None


class UnifiedProbe:
    """Unified probe interface for both files/streams and webcams."""
    
    def __init__(self, ffprobe_path: str = "ffprobe"):
        """Initialize with FFProbe for file/stream probing."""
        self.ffprobe = FFProbe(ffprobe_path)
        self.webcam_probe = WebcamProbe()
    
    def probe(self, source: Union[str, int]) -> Union[VideoInfo, WebcamInfo]:
        """
        Probe video source (file, URL, or webcam).
        
        Args:
            source: Either a string (file path/URL) or int (webcam device ID)
            
        Returns:
            VideoInfo for files/streams, WebcamInfo for webcams
        """
        if isinstance(source, int):
            # Webcam device
            return self.webcam_probe.probe(source)
        else:
            # File or stream
            return self.ffprobe.probe(source)
    
    def get_resolution(self, info: Union[VideoInfo, WebcamInfo]) -> tuple[int, int]:
        """Get resolution from either type of info."""
        if isinstance(info, WebcamInfo):
            return (info.width, info.height)
        else:
            video_stream = self.ffprobe.get_primary_video_stream(info)
            if video_stream:
                return (video_stream.width or 0, video_stream.height or 0)
        return (0, 0)
    
    def get_fps(self, info: Union[VideoInfo, WebcamInfo]) -> float:
        """Get FPS from either type of info."""
        if isinstance(info, WebcamInfo):
            return info.fps
        else:
            video_stream = self.ffprobe.get_primary_video_stream(info)
            return video_stream.fps if video_stream else 0.0
    
    def get_codec(self, info: Union[VideoInfo, WebcamInfo]) -> str:
        """Get video codec from either type of info."""
        if isinstance(info, WebcamInfo):
            return info.fourcc
        else:
            video_stream = self.ffprobe.get_primary_video_stream(info)
            return video_stream.codec_name if video_stream else ""