# Configuration Examples

This directory contains example configuration files for different use cases of the cvkitworker system.

## Configuration Files

### `config.sample.json`
**Basic RTSP streaming configuration**
- **Purpose**: Template for setting up RTSP camera streams with face detection
- **Input Source**: RTSP camera stream (IP camera)
- **Detectors**: Multiple face detection stages (detection, matching, liveness)
- **Actions**: HTTP notification webhook
- **Use Case**: Production surveillance system with IP cameras
- **Key Features**:
  - RTSP stream input with authentication
  - Multi-stage face detection pipeline
  - HTTP webhook notifications
  - YOLO-based detection models

### `config.video.json`
**Video file input configuration**
- **Purpose**: Process video files for testing and analysis
- **Input Source**: Local video file (.mp4, .avi, etc.)
- **Detectors**: CNN-based face detection (dlib_cnn)
- **Preprocessing**: Frame resizing to 640x480
- **Use Case**: Testing face detection on recorded video files
- **Key Features**:
  - File-based video input
  - Frame preprocessing and resizing
  - High-accuracy CNN face detection
  - No external notifications (testing focused)

### `config.timing.json`
**Performance monitoring configuration**
- **Purpose**: Webcam input with detailed timing measurement
- **Input Source**: System webcam (camera index 0)
- **Detectors**: Face detection with timing analysis
- **Timing Features**: Comprehensive performance monitoring
- **Use Case**: Performance testing and optimization
- **Key Features**:
  - Webcam live input
  - Detailed timing measurement system
  - JSON Lines logging format
  - Function argument and result tracking
  - Performance analysis capabilities

## Usage Examples

### Basic RTSP Setup
```bash
# Copy and customize for your camera
cp examples/config.sample.json config.json
# Edit the RTSP URL with your camera details
cvkitworker --config config.json
```

### Video File Testing
```bash
# Test with a video file
cp examples/config.video.json config.json
# Update the file_path to your video
cvkitworker --config config.json
```

### Performance Analysis
```bash
# Enable timing measurements with webcam
cp examples/config.timing.json config.json
cvkitworker --config config.json
# View timing results in logs/timing_measurements.jsonl
```

### Quick Start Options
```bash
# Auto-generate webcam config
cvkitworker --webcam

# Auto-generate video file config  
cvkitworker --file /path/to/video.mp4

# Enable timing with environment variable
CVKIT_TIMING_ENABLED=true cvkitworker --webcam
```

## Configuration Structure

All configuration files follow the same JSON structure:

```json
{
  "receivers": [     // Input sources (RTSP, webcam, video files)
    {...}
  ],
  "preprocessors": [ // Frame preprocessing steps (resize, grayscale)
    {...}
  ],
  "detectors": [     // Computer vision detection algorithms
    {...}
  ],
  "actions": [       // Output actions (HTTP, logging, alerts)
    {...}
  ],
  "timing": {        // Performance monitoring (optional)
    ...
  }
}
```

## Detector Types Available

- **`dlib`**: Fast Haar cascade face detection
- **`dlib_cnn`**: High-accuracy CNN face detection
- **`opencv_dnn`**: OpenCV DNN face detection
- **`yunet`**: YuNet face detection model

## Input Source Types

- **`rtsp`**: IP camera RTSP streams
- **`webcam`**: Local system cameras
- **`video`**: Video file input (.mp4, .avi, .mov, etc.)

## Performance Monitoring

The timing configuration enables detailed performance analysis:

- **Function-level timing**: Measure individual CV operations
- **Context capture**: Record function arguments and results
- **Storage options**: File, database, or telemetry systems
- **Zero overhead**: No performance impact when disabled

See `docs/timing_measurement.md` for detailed timing system documentation.