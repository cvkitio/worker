# Timing Measurement System

The cvkitworker includes a comprehensive timing measurement system for monitoring performance of computer vision operations.

## Features

- **Decorator-based timing**: Easy to add timing to any function
- **Multiple storage backends**: File, Database (future), Telemetry (future)
- **Configurable activation**: Environment variables or config file
- **Detailed context**: Function arguments, results, process info
- **Zero overhead when disabled**: No performance impact when timing is off

## Configuration

### Environment Variables

```bash
# Enable timing measurement
export CVKIT_TIMING_ENABLED=true

# Set storage backend (file, database, telemetry)
export CVKIT_TIMING_STORAGE=file

# Set output file path (for file storage)
export CVKIT_TIMING_FILE=logs/timing_measurements.jsonl

# Database connection (for database storage - future)
export CVKIT_TIMING_DB_CONNECTION="postgresql://user:pass@host:port/db"

# Telemetry endpoint (for telemetry storage - future)
export CVKIT_TIMING_TELEMETRY_ENDPOINT="https://telemetry.example.com/api/metrics"
export CVKIT_TIMING_TELEMETRY_API_KEY="your-api-key"
```

### Config File

Add timing configuration to your config.json:

```json
{
  "timing": {
    "enabled": true,
    "storage": "file",
    "file_path": "logs/timing_measurements.jsonl",
    "include_args": true,
    "include_results": true
  }
}
```

## Usage Examples

### Basic Usage

```bash
# Enable timing and run with webcam
CVKIT_TIMING_ENABLED=true cvkitworker --webcam

# Use config file with timing enabled
cvkitworker --config config.timing.json
```

### Output Format

Timing measurements are stored as JSON lines:

```json
{
  "timestamp": "2025-06-12T22:40:39.351071",
  "function": "face_detection",
  "duration_ms": 25.5,
  "process_id": 12345,
  "context": {
    "module": "cvkitworker.detectors.detectors.face_detect",
    "class": "FaceDetector",
    "args": ["array(480, 640, 3)"],
    "result_length": 1
  }
}
```

## Measured Operations

The following computer vision operations are automatically measured:

- **Face Detection**: `@measure_face_detection`
  - Main detection algorithms (dlib, dlib_cnn, opencv_dnn, yunet)
  - Includes detected face count in results

- **Color Space Conversion**: `@measure_color_conversion`
  - BGR to RGB conversions for dlib
  - Grayscale conversions
  - Any cv2.cvtColor operations

- **Image Scaling**: `@measure_scaling`
  - Frame resizing operations
  - Preprocessing scale changes

- **Frame Processing**: `@measure_frame_processing`
  - Overall frame preprocessing pipeline
  - Multi-step processing chains

- **Image Processing**: `@measure_image_processing`
  - DNN blob creation
  - Other OpenCV image operations

## Storage Backends

### File Storage (Current)

- **Format**: JSON Lines (.jsonl)
- **Location**: Configurable file path
- **Rotation**: Manual (future: automatic rotation)
- **Performance**: Low overhead, immediate writes

### Database Storage (Future)

- **Databases**: PostgreSQL, MySQL, SQLite
- **Schema**: Structured timing tables
- **Querying**: SQL-based analysis
- **Retention**: Configurable retention policies

### Telemetry Storage (Future)

- **Targets**: Prometheus, InfluxDB, CloudWatch, DataDog
- **Aggregation**: Real-time metrics aggregation
- **Alerting**: Performance threshold alerts
- **Dashboards**: Grafana, CloudWatch dashboards

## Performance Analysis

### Reading Timing Data

```python
import json

with open('logs/timing_measurements.jsonl', 'r') as f:
    measurements = [json.loads(line) for line in f]

# Analyze face detection performance
face_detections = [m for m in measurements if m['function'] == 'face_detection']
avg_duration = sum(m['duration_ms'] for m in face_detections) / len(face_detections)
print(f"Average face detection time: {avg_duration:.2f}ms")
```

### Common Metrics

- **Face Detection Latency**: Time per detection operation
- **Frame Processing Throughput**: Frames processed per second
- **Color Conversion Overhead**: RGB/BGR conversion costs
- **Scaling Performance**: Resize operation efficiency
- **Process Distribution**: Performance across worker processes

## Best Practices

1. **Enable Only When Needed**: Timing has minimal but non-zero overhead
2. **Monitor File Growth**: Timing logs can grow large over time
3. **Aggregate for Analysis**: Use tools like pandas for data analysis
4. **Set Appropriate Storage**: File for development, DB/telemetry for production
5. **Regular Cleanup**: Rotate or archive old timing files

## Troubleshooting

### Timing Not Working

1. Check `CVKIT_TIMING_ENABLED` environment variable
2. Verify config file timing section
3. Check file permissions for output directory
4. Ensure logs directory exists

### Large Log Files

1. Implement log rotation
2. Use database storage for production
3. Filter measurements by operation type
4. Aggregate data before storage

### Performance Impact

1. Disable timing in production if not needed
2. Use sampling for high-frequency operations
3. Monitor storage backend performance
4. Consider asynchronous storage writes