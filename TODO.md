# TODO List

## AI Functions
- [ ] Add YoloE as a detection model

## Video processing
- [ ] Complete the implementation of storing frams to a circular buffer
- [ ] Add scene change detection for the first step in initiating a processing chain

## Notifications
- [ ] Add a function to send notifications to an endpoint when an event is detected. Start with sending to Firebase

## Refactoring
- [ ] Finish moving to the new structure in cvkitworker/refactor. Come up with a separate plan on how to introduce that

## CI/CD Improvements
- [ ] Consider using pre-built dlib wheels or Docker images
- [ ] Investigate alternative face detection libraries that are faster to install
- [ ] Split tests into unit and integration tests with separate workflows
- [ ] Add matrix strategy to test different components separately

## Phase 1: Testing Infrastructure (Priority: Critical)
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

## Phase 2: Error Handling & Robustness (Priority: High)
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

## Phase 3: CLI Enhancements (Priority: Medium)
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

## Phase 4: Configuration Management (Priority: Medium)
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

## Phase 5: Code Organization (Priority: Low)
**Status: Planned**

- [ ] **Enhanced package structure**
  - Standalone detection module organization
  - Cleaner import structure and module separation
  - Improved detector loading and initialization
  - Performance monitoring and logging improvements