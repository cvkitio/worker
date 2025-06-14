import pytest
import tempfile
import subprocess
import time
import json
from pathlib import Path
from cvkitworker.utils.probe import FFProbe, VideoInfo, StreamInfo
from unittest.mock import patch, MagicMock


class TestFFProbe:
    @pytest.fixture
    def ffprobe(self):
        """Create FFProbe instance."""
        return FFProbe()
    
    @pytest.fixture
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
    
    @pytest.mark.slow
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
    
    @pytest.mark.slow
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
    
    @pytest.mark.slow
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
    
    @patch('subprocess.run')
    def test_probe_rtsp_url_mocked(self, mock_run, ffprobe):
        """Test that probe can handle RTSP URLs (mocked)."""
        # Mock ffprobe output for an RTSP stream
        mock_output = {
            "format": {
                "filename": "rtsp://localhost:8554/test",
                "format_name": "rtsp",
                "format_long_name": "RTSP input",
                "duration": "0.000000",
                "size": "0",
                "bit_rate": "0",
                "nb_streams": 1
            },
            "streams": [{
                "index": 0,
                "codec_name": "h264",
                "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
                "codec_type": "video",
                "width": 640,
                "height": 480,
                "coded_width": 640,
                "coded_height": 480,
                "pix_fmt": "yuv420p",
                "avg_frame_rate": "30/1",
                "time_base": "1/90000"
            }]
        }
        
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(mock_output)
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Test probing RTSP URL
        info = ffprobe.probe("rtsp://localhost:8554/test")
        
        # Verify results
        assert isinstance(info, VideoInfo)
        assert info.filename == "rtsp://localhost:8554/test"
        assert info.format_name == "rtsp"
        assert info.nb_streams == 1
        
        # Check video stream
        video_stream = ffprobe.get_primary_video_stream(info)
        assert video_stream is not None
        assert video_stream.codec_type == "video"
        assert video_stream.codec_name == "h264"
        assert video_stream.width == 640
        assert video_stream.height == 480
    
    def test_probe_invalid_rtsp_url(self, ffprobe):
        """Test that probe fails gracefully on invalid RTSP URL."""
        # This should fail quickly without hanging
        with pytest.raises(RuntimeError, match="Failed to probe video"):
            # Use a non-routable IP to ensure quick failure
            ffprobe.probe("rtsp://192.0.2.1:554/invalid")
    
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