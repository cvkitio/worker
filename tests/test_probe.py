import pytest
import tempfile
import subprocess
from pathlib import Path
from cvkitworker.utils.probe import FFProbe, VideoInfo, StreamInfo


class TestFFProbe:
    @pytest.fixture
    def ffprobe(self):
        """Create FFProbe instance."""
        return FFProbe()
    
    @pytest.fixture
    @pytest.mark.slow
    def sample_video(self):
        """Create a simple test video using ffmpeg."""
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
            video_path = f.name
        
        # Create a 2-second test video with ffmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f", "lavfi",
            "-i", "testsrc=duration=2:size=640x480:rate=30",  # Test pattern
            "-f", "lavfi", 
            "-i", "sine=frequency=1000:duration=2",  # Test audio
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:v", "1M",
            "-b:a", "128k",
            video_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            yield video_path
        finally:
            Path(video_path).unlink(missing_ok=True)
    
    def test_probe_video_metadata(self, ffprobe, sample_video):
        """Test extracting metadata from video file."""
        info = ffprobe.probe(sample_video)
        
        # Check basic format info
        assert isinstance(info, VideoInfo)
        assert info.filename == sample_video
        assert info.format_name == "mov,mp4,m4a,3gp,3g2,mj2"
        assert info.duration > 0
        assert info.duration < 3  # Should be around 2 seconds
        assert info.bit_rate > 0
        assert info.nb_streams >= 2  # At least video and audio
        
        # Check streams
        assert len(info.streams) >= 2
        video_streams = ffprobe.get_video_streams(info)
        audio_streams = ffprobe.get_audio_streams(info)
        
        assert len(video_streams) >= 1
        assert len(audio_streams) >= 1
    
    def test_video_stream_info(self, ffprobe, sample_video):
        """Test video stream specific information."""
        info = ffprobe.probe(sample_video)
        video_stream = ffprobe.get_primary_video_stream(info)
        
        assert video_stream is not None
        assert video_stream.codec_type == "video"
        assert video_stream.codec_name == "h264"
        assert video_stream.width == 640
        assert video_stream.height == 480
        assert video_stream.fps is not None
        assert 29 <= video_stream.fps <= 31  # Should be close to 30 fps
        assert video_stream.pix_fmt is not None
    
    def test_audio_stream_info(self, ffprobe, sample_video):
        """Test audio stream specific information."""
        info = ffprobe.probe(sample_video)
        audio_stream = ffprobe.get_primary_audio_stream(info)
        
        assert audio_stream is not None
        assert audio_stream.codec_type == "audio"
        assert audio_stream.codec_name == "aac"
        assert audio_stream.sample_rate > 0
        assert audio_stream.channels > 0
    
    def test_probe_invalid_file(self, ffprobe):
        """Test probing non-existent file raises error."""
        with pytest.raises(RuntimeError, match="Failed to probe video"):
            ffprobe.probe("/non/existent/file.mp4")
    
    def test_probe_rtsp_url(self, ffprobe):
        """Test that probe can handle URLs (will fail but test structure)."""
        # This will fail since we don't have a real RTSP server
        # but it tests that the probe accepts URL paths
        with pytest.raises(RuntimeError):
            ffprobe.probe("rtsp://example.com/stream")
    
    @pytest.mark.skipif(
        subprocess.run(["which", "ffprobe"], capture_output=True).returncode != 0,
        reason="ffprobe not installed"
    )
    def test_ffprobe_availability(self):
        """Test that ffprobe is available on the system."""
        ffprobe = FFProbe()  # Should not raise
        assert ffprobe.ffprobe_path == "ffprobe"
    
    def test_custom_ffprobe_path(self):
        """Test using custom ffprobe path."""
        with pytest.raises(RuntimeError, match="ffprobe not found"):
            FFProbe(ffprobe_path="/non/existent/ffprobe")