# FrameChain Refactor

This directory contains a refactored framechain implementation for multi-processor video frame processing.

## Architecture

The framechain follows a pipeline architecture:
- **PreProcessor**: Frame preprocessing (scale, resize, color conversion, etc.)
- **Detector**: Computer vision detection (face detection, object detection, etc.)
- **Markuper**: Visual markup of detection results (bounding boxes, labels, etc.)
- **Outputer**: Output handling (file saving, streaming, display, etc.)

## Usage

```python
from framechain.core import ProcessorChain
from framechain.preprocessors import Scale
from framechain.detectors import FaceDetector
from framechain.markupers import FaceMarkup
from framechain.outputers import OutputFile

# Create processing chain
chain = ProcessorChain([
    Scale(0.5),
    FaceDetector(),
    FaceMarkup(),
    OutputFile("output.jpg")
])

# Process a frame
result = chain.run(frame)
```

## Testing

Run the test suite:
```bash
python test_framechain.py
```

Run the multiprocessing pipeline:
```bash
python main.py
FRAMECHAIN_NUM_FRAMES=5 python main.py
```

## Implementation Status

✅ Complete processor architecture with abstract base classes
✅ ProcessorChain implementation with metadata flow
✅ Multiprocessing support with shared memory
✅ Mock implementations for all processor types
✅ Comprehensive test suite
✅ Automatic cleanup and error handling

This serves as a foundation for enhanced video processing capabilities while remaining isolated from the main application.