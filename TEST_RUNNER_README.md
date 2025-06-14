# Test Runner Guide

## Quick Start

```bash
# Run fast unit tests (recommended for development)
python run_tests.py --unit

# Run fastest tests only (30 second max)
python run_tests.py --fast

# Run with coverage
python run_tests.py --unit --coverage

# List available test categories
python run_tests.py --list
```

## Test Categories

### ⚡ Fast Tests (`--fast`)
- **Time**: ~5-10 seconds
- **Purpose**: Quick validation during development
- **Includes**: Core functionality, mocked tests
- **Excludes**: Video processing, file I/O, slow operations

### 🏃 Unit Tests (`--unit`) 
- **Time**: ~10-30 seconds  
- **Purpose**: Test individual components
- **Includes**: All unit tests, some probe tests
- **Excludes**: Integration tests, video processing

### 🔗 Integration Tests (`--integration`)
- **Time**: ~5-10 minutes
- **Purpose**: End-to-end testing
- **Includes**: Video processing, full application runs
- **Warning**: May timeout in CI environments

### 🎥 Video Tests (`--video`)
- **Time**: ~10-15 minutes
- **Purpose**: Video processing specific tests
- **Requires**: FFmpeg, test video files
- **Note**: Subset of integration tests

### 🐌 Slow Tests (`--slow`)
- **Time**: ~2-5 minutes
- **Purpose**: Tests that create videos or files
- **Includes**: FFmpeg video creation, file I/O

## Examples

```bash
# Development workflow
python run_tests.py --fast           # Quick validation
python run_tests.py --unit           # Before committing

# CI/Testing workflow  
python run_tests.py --unit --coverage # CI unit tests
python run_tests.py --integration     # Nightly builds

# Debugging
python run_tests.py --video --verbose # Debug video issues
python run_tests.py --slow            # Test file operations
```

## Test Structure

```
tests/
├── test_probe.py              # Unit + slow tests
├── test_resize_aspect_ratio.py # Unit tests
├── test_timing.py             # Unit tests  
├── test_worker_config.py      # Unit tests
├── test_video_integration.py  # Integration + video tests
├── test_video_processing.py   # Integration + video tests
└── test_video_simple.py       # Integration + video tests
```

## Pytest Markers

Tests are marked with the following categories:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - End-to-end tests
- `@pytest.mark.video` - Video processing tests
- `@pytest.mark.slow` - Tests requiring file/video creation

## Running Tests Manually

If you prefer using pytest directly:

```bash
# Unit tests only
pytest -m "not integration and not slow" -v

# Integration tests only  
pytest -m "integration" -v --timeout=300

# Specific test file
pytest tests/test_resize_aspect_ratio.py -v

# With coverage
pytest -m "not integration and not slow" --cov=src/cvkitworker --cov-report=html
```

## Troubleshooting

### Tests Timeout
- Use `--timeout` flag to increase timeout
- Video tests may need 10+ minutes
- Check if FFmpeg is installed and working

### Missing Dependencies
- Run `pip install -e ".[dev]"` to install test dependencies
- Ensure FFmpeg is installed for video tests

### CI Failures
- Use `--unit` for fast CI builds
- Run `--integration` only in nightly/release builds
- Video tests may not work in headless CI environments

## Performance Tips

- Use `--fast` during active development
- Run `--unit` before commits
- Schedule `--integration` tests separately
- Use `--coverage` only when needed (slower)