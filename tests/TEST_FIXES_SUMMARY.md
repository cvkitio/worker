# Test Fixes Summary

## 1. RTSP Probe Test Fix

### Problem
The `test_probe_rtsp_url` test was hanging indefinitely because ffprobe was trying to connect to a non-existent RTSP server and timing out.

### Solution
- Added a 5-second timeout to ffprobe command (`-timeout 5000000`)
- Created a mocked version of the RTSP test (`test_probe_rtsp_url_mocked`) that doesn't require a real RTSP server
- Added `test_probe_invalid_rtsp_url` that uses a non-routable IP address to ensure quick failure
- Removed the complex RTSP server dependencies in favor of mocking

### Files Changed
- `src/cvkitworker/utils/probe.py` - Added timeout to ffprobe command
- `tests/test_probe.py` - Added mocked RTSP test and invalid URL test
- `pyproject.toml` - Added pytest-timeout to dev dependencies

## 2. Resize Function Tests ✅ FIXED

### Problem
The `test_resize_aspect_ratio.py` tests were failing because they were trying to call `self.frame_worker._resize_frame()` but this method was moved to `cvkitworker.preprocessors.image_processing` module during the preprocessor refactor.

### Solution Applied
- Added import: `from cvkitworker.preprocessors.image_processing import resize_frame, convert_to_grayscale`
- Updated all test calls from `self.frame_worker._resize_frame()` to `resize_frame()`
- All 7 resize tests now pass

### Files Changed
- `tests/test_resize_aspect_ratio.py` - Updated imports and function calls

## 3. Video Integration Tests

### Problem
Video integration tests in `test_video_integration.py` are timing out, likely due to actual video processing pipelines.

### Solution Options
1. Mark these tests with `@pytest.mark.slow`
2. Add shorter timeouts with `@pytest.mark.timeout(30)`
3. Mock the video processing parts
4. Run only in non-CI environments

## 4. Pytest Configuration

### Problem
Warning about unknown config option `timeout` in pytest.ini

### Solution
- pytest-timeout has been added to dev dependencies
- The warning should disappear after reinstalling dependencies