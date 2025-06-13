import cv2
from typing import Dict, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class WebcamInfo:
    """Information about a webcam device."""
    device_id: int
    width: int
    height: int
    fps: float
    backend: str
    fourcc: str
    is_opened: bool
    
    # OpenCV property values
    brightness: Optional[float] = None
    contrast: Optional[float] = None
    saturation: Optional[float] = None
    exposure: Optional[float] = None
    
    @property
    def resolution_str(self) -> str:
        """Return resolution as string."""
        return f"{self.width}x{self.height}"


class WebcamProbe:
    """Utility class to extract webcam metadata using OpenCV."""
    
    @staticmethod
    def probe(device_id: int = 0) -> WebcamInfo:
        """
        Extract metadata from webcam device.
        
        Args:
            device_id: Webcam device ID (default: 0)
            
        Returns:
            WebcamInfo object containing webcam properties
            
        Raises:
            RuntimeError: If webcam cannot be opened
        """
        # Try to open webcam
        cap = cv2.VideoCapture(device_id)
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open webcam device {device_id}")
        
        try:
            # Get basic properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            # Convert fourcc to string
            fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            # Get backend name
            backend = cap.getBackendName()
            
            # Try to get camera settings (may not be supported on all devices)
            brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
            contrast = cap.get(cv2.CAP_PROP_CONTRAST)
            saturation = cap.get(cv2.CAP_PROP_SATURATION)
            exposure = cap.get(cv2.CAP_PROP_EXPOSURE)
            
            # Clean up values (-1 typically means not supported)
            brightness = brightness if brightness != -1 else None
            contrast = contrast if contrast != -1 else None
            saturation = saturation if saturation != -1 else None
            exposure = exposure if exposure != -1 else None
            
            return WebcamInfo(
                device_id=device_id,
                width=width,
                height=height,
                fps=fps,
                backend=backend,
                fourcc=fourcc_str,
                is_opened=True,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                exposure=exposure
            )
            
        finally:
            cap.release()
    
    @staticmethod
    def list_available_webcams(max_devices: int = 10) -> Dict[int, bool]:
        """
        List available webcam devices.
        
        Args:
            max_devices: Maximum number of devices to check
            
        Returns:
            Dict mapping device ID to availability
        """
        available = {}
        
        for i in range(max_devices):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available[i] = True
                cap.release()
            else:
                available[i] = False
                
        return {k: v for k, v in available.items() if v}
    
    @staticmethod
    def set_resolution(device_id: int, width: int, height: int) -> bool:
        """
        Try to set webcam resolution.
        
        Args:
            device_id: Webcam device ID
            width: Desired width
            height: Desired height
            
        Returns:
            True if resolution was set successfully
        """
        cap = cv2.VideoCapture(device_id)
        
        if not cap.isOpened():
            return False
        
        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Verify the resolution was actually set
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            return actual_width == width and actual_height == height
            
        finally:
            cap.release()
    
    @staticmethod
    def get_supported_resolutions(device_id: int) -> list:
        """
        Try common resolutions to see what's supported.
        
        Args:
            device_id: Webcam device ID
            
        Returns:
            List of supported (width, height) tuples
        """
        common_resolutions = [
            (640, 480),    # VGA
            (800, 600),    # SVGA
            (1280, 720),   # HD
            (1920, 1080),  # Full HD
            (1024, 768),   # XGA
            (1280, 960),   # SXGA
            (1600, 1200),  # UXGA
        ]
        
        supported = []
        cap = cv2.VideoCapture(device_id)
        
        if not cap.isOpened():
            return supported
        
        try:
            # Save original resolution
            orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            for width, height in common_resolutions:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                if (actual_width, actual_height) == (width, height):
                    supported.append((width, height))
            
            # Restore original resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, orig_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, orig_height)
            
        finally:
            cap.release()
        
        return sorted(set(supported))  # Remove duplicates and sort