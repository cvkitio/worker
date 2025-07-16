import cv2
from ..utils.timing import measure_scaling, measure_color_conversion


@measure_scaling
def resize_frame(frame, width, height):
    """Resize frame with timing measurement, maintaining aspect ratio.
    
    If only width is provided (height=None), scale to that width.
    If only height is provided (width=None), scale to that height.
    If both are provided, use the old behavior (may distort image).
    """
    orig_height, orig_width = frame.shape[:2]
    
    if width is not None and height is None:
        # Scale by width, maintain aspect ratio
        scale_factor = width / orig_width
        new_height = int(orig_height * scale_factor)
        return cv2.resize(frame, (width, new_height))
    elif height is not None and width is None:
        # Scale by height, maintain aspect ratio
        scale_factor = height / orig_height
        new_width = int(orig_width * scale_factor)
        return cv2.resize(frame, (new_width, height))
    else:
        # Both provided or both None - use original behavior
        if width is None and height is None:
            return frame
        return cv2.resize(frame, (width, height))


@measure_color_conversion
def convert_to_grayscale(frame):
    """Convert frame to grayscale with timing measurement."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)