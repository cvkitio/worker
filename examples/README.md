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

### `config.aspect_ratio.json`
**Aspect ratio preserving resize configuration**
- **Purpose**: Demonstrate the new aspect ratio preserving resize functionality
- **Input Source**: System webcam (camera index 0)
- **Preprocessing**: Resize to specific width while maintaining aspect ratio
- **Use Case**: Processing video streams without distorting images
- **Key Features**:
  - Specify only width OR height in resize preprocessor
  - Automatically calculates the other dimension to maintain aspect ratio
  - Prevents image distortion during preprocessing
  - Useful for standardizing input sizes without squashing images

### `config.workers.json`
**Multi-worker configuration for high-performance processing**
- **Purpose**: Demonstrate configurable worker count for parallel processing
- **Input Source**: System webcam (camera index 0)
- **Worker Configuration**: 4 detect workers for parallel face detection
- **Use Case**: High-throughput video processing with multiple worker processes
- **Key Features**:
  - Configurable worker count (4 detect workers)
  - Parallel face detection processing
  - Optimized for multi-core systems
  - Higher processing throughput
  - Load balancing across worker processes

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

# Debug camera issues (enumerate all available cameras)
CVKIT_ENUMERATE_CAMERAS=true cvkitworker --webcam

# Configure worker count via environment variable
CVKIT_WORKERS=4 cvkitworker --webcam

# Override worker count via CLI argument
cvkitworker --webcam --workers 6
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
  },
  "workers": {       // Worker process configuration (optional)
    "detect_workers": 4,    // Number of detection worker processes
    "frame_workers": 1      // Number of frame worker processes (always 1)
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

## Preprocessing Options

### Resize Preprocessor

The resize preprocessor now supports aspect ratio preservation:

```json
{
  "preprocessors": [
    {
      "name": "resize_by_width",
      "type": "resize",
      "width": 640
      // Height will be calculated automatically
    }
  ]
}
```

**Resize Modes:**
- **Width only**: Specify `"width"` - height is calculated to maintain aspect ratio
- **Height only**: Specify `"height"` - width is calculated to maintain aspect ratio  
- **Both dimensions**: Specify both `"width"` and `"height"` - may distort the image
- **Neither dimension**: Omit both - returns the original frame unchanged

**Example configurations:**
```json
// Scale to 640px width, maintain aspect ratio
{"type": "resize", "width": 640}

// Scale to 480px height, maintain aspect ratio
{"type": "resize", "height": 480}

// Scale to exact 640x480 (may distort)
{"type": "resize", "width": 640, "height": 480}
```

### Grayscale Preprocessor

Converts frames to grayscale:
```json
{"type": "grayscale"}
```

## Worker Configuration

The system uses a producer-consumer architecture with configurable worker processes:

### Worker Types

- **Frame Workers** (1): Producer process that reads video frames and applies preprocessing
- **Detect Workers** (configurable): Consumer processes that perform face detection on frames

### Configuration Priority

Worker count is determined in this priority order:

1. **CLI Argument**: `--workers N` (highest priority)
2. **Environment Variable**: `CVKIT_WORKERS=N`
3. **Config File**: `"workers": {"detect_workers": N}`
4. **Default**: 2 detect workers

### Configuration Examples

```json
{
  "workers": {
    "detect_workers": 4
  }
}
```

```bash
# Environment variable
export CVKIT_WORKERS=6
cvkitworker --webcam

# CLI override
cvkitworker --config config.json --workers 8
```

### Performance Recommendations

- **Single CPU core**: Use 1-2 detect workers
- **Dual core**: Use 2-3 detect workers  
- **Quad core**: Use 3-4 detect workers
- **8+ cores**: Use 4-8 detect workers

Higher worker counts may not improve performance due to:
- Model loading overhead
- Memory bandwidth limitations
- GIL constraints in face detection libraries

## Performance Monitoring

The timing configuration enables detailed performance analysis:

- **Function-level timing**: Measure individual CV operations
- **Context capture**: Record function arguments and results
- **Storage options**: File, database, or telemetry systems
- **Zero overhead**: No performance impact when disabled

See `docs/timing_measurement.md` for detailed timing system documentation.

## Camera Troubleshooting

### macOS Camera Issues

**Continuity Camera Warning**: On macOS, you may see a deprecation warning about AVCaptureDeviceTypeExternal. This is normal and the camera will still work properly.

**Camera Access Permissions**: Ensure your terminal application has camera access permissions in System Preferences > Security & Privacy > Camera.

**Multiple Cameras**: Use `CVKIT_ENUMERATE_CAMERAS=true` to see all available cameras and their indices.

### Camera Selection

```json
{
  "receivers": [
    {
      "name": "webcam_input", 
      "type": "webcam",
      "source": 1  // Try different indices (0, 1, 2) for different cameras
    }
  ]
}
```

### Common Camera Indices
- **0**: Built-in camera (MacBook camera)
- **1**: External USB camera or Continuity Camera
- **2**: Additional external cameras

### Camera Backend Selection
The system automatically uses the best backend for your platform:
- **macOS**: AVFoundation backend (recommended)
- **Windows**: DirectShow backend  
- **Linux**: V4L2 backend