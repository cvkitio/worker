# cvkit.io worker

A worker for performing real time computer vision related operations and generating events optimized to run as a container.

One of the key considerations for this package is that it can manage complex chains of computer vision tasks without blocking the main frame processing loop.

Some examples:

1. Are there faces in the frame?
    --> Yes, extract the faces
        --> Is the face live?
            --> For each face does it match an entry in a face DB
                --> If we get a match send a notification

2. Are there cars in the frame?
    --> Yes, extract the cars
        --> Extract the car features
            --> Does the car have a numberplate?
                --> If the number plate matches a DB entry send a notification

## Components

![High Level Overview](docs/high_level_overview.png)

## Installation

### Development Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in development mode
pip install -e .
```

### Production Installation

```bash
pip install cvkitworker
```

### CI/CD Status

⚠️ **Note**: GitHub Actions CI tests are currently failing due to timeout issues with dlib compilation. This needs to be addressed:

**TODO**:
- [ ] Consider using pre-built dlib wheels or Docker images
- [ ] Investigate alternative face detection libraries that are faster to install
- [ ] Split tests into unit and integration tests with separate workflows
- [ ] Add matrix strategy to test different components separately

The tests pass locally but timeout in CI due to the long compilation time of dlib from source.

## Usage

After installation, you can run the application in several ways:

```bash
# Using the installed CLI command
cvkitworker --config config.sample.json

# Or as a Python module
python -m cvkitworker --config config.sample.json
```

## Development Roadmap

This project is being incrementally improved with features from the `feature/improve-structure` branch. The implementation plan prioritizes testing infrastructure first, followed by reliability improvements.

### Phase 1: Testing Infrastructure (Priority: Critical)
**Status: Planned**

- [ ] **Add comprehensive testing framework**
  - Automated face detection accuracy testing using Kaggle human faces dataset
  - Ground truth validation with metadata-driven testing
  - Performance benchmarking (timing and accuracy metrics)
  - Support for both positive (faces) and negative (blanks) test cases

- [ ] **Test data management**
  - Automated test dataset creation and download
  - Kaggle API integration for human faces dataset
  - Test video management and organization
  - Proper .gitignore updates for test data

- [ ] **Testing utilities**
  - `tests/test_kaggle_face_detection.py` - Main testing framework
  - `tests/create_kaggle_test_dataset.py` - Dataset creation utilities
  - `tests/download_kaggle_faces.py` - Kaggle dataset downloader
  - `tests/download_test_videos.py` - Test video management

**Benefits**: Immediate validation of system functionality, automated performance monitoring, confidence in code changes

### Phase 2: Error Handling & Robustness (Priority: High)
**Status: Planned**

- [ ] **Enhanced frame processing reliability**
  - Consecutive failure tracking with configurable thresholds
  - Graceful recovery from temporary stream interruptions
  - Enhanced logging for debugging connection issues
  - Retry logic with exponential backoff for RTSP streams

- [ ] **Robust receiver validation**
  - RTSP connection validation with frame reading tests
  - Webcam device validation and error reporting
  - Video file existence and format validation
  - Connection timeout and retry mechanisms

**Benefits**: Production-ready reliability, better debugging capabilities, reduced downtime

### Phase 3: CLI Enhancements (Priority: Medium)
**Status: Planned**

- [ ] **Convenient CLI flags**
  - `--webcam` flag for instant testing without config files
  - `--video` flag for video file processing
  - Automatic configuration generation for common use cases
  - Improved argument parsing and help text

- [ ] **Performance optimizations**
  - 640x480 default resolution for 3x speed improvement
  - Optimized detector frequency settings
  - Memory-efficient frame processing

**Benefits**: Better developer experience, faster testing cycles, optimized performance

### Phase 4: Configuration Management (Priority: Medium)
**Status: Planned**

- [ ] **Enhanced configuration support**
  - YAML configuration format support
  - Better validation and error reporting
  - Hierarchical detector relationships (parent-child)
  - Flexible preprocessor chains

- [ ] **Configuration templates**
  - `config.webcam.json` - Webcam-specific configuration
  - `config.sample.yaml` - YAML format examples
  - `config.bad_rtsp.json` - Troubleshooting examples

**Benefits**: More flexible configuration options, better error handling, easier setup

### Phase 5: Code Organization (Priority: Low)
**Status: Planned**

- [ ] **Enhanced package structure**
  - Standalone detection module organization
  - Cleaner import structure and module separation
  - Improved detector loading and initialization
  - Performance monitoring and logging improvements

**Benefits**: Better code maintainability, clearer separation of concerns

### Implementation Notes

- Each phase will be implemented incrementally with thorough testing
- Testing infrastructure (Phase 1) provides foundation for validating all subsequent changes
- Error handling improvements (Phase 2) are critical for production deployment
- CLI enhancements (Phase 3) improve developer productivity
- Later phases focus on flexibility and maintainability

### Current Status
- ✅ Package restructure complete (can run with `python -m cvkitio_worker`)
- 🔄 Ready to begin Phase 1: Testing Infrastructure

## How it works

The server will need a config file that defines

```json
{
    "receiver":{
        "type" : "rtsp|webrtc|http",
        "source" : "http://server/somefile.mp4"
    },
    "detectors":[
        {
            "type" : "humanoid",
            "variant" : "yolo",
            "frequency_ms" : 500,
            "actions" : [
                {
                    "type" : "sms",
                    "destination" : "+1234567890"
                },
                {
                    "type" : "email",
                    "destination" : "email@example.com"
                }
            ]
        }
    ]


```

## Initial test scenarios

1. Detect a humanoid and send an email
