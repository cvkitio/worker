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

`python -m venv .venv`

`source .venv/bin/activate`

`pip install -r requirements.txt`  



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

## Testing

### Download Test Data

To download test data including Kaggle face datasets and test videos:

```bash
# Download Kaggle faces dataset (requires Kaggle API credentials)
python tests/download_kaggle_faces.py

# Download test videos
python tests/download_test_videos.py

# Create test dataset from Kaggle faces
python tests/create_kaggle_test_dataset.py
```

### Run Tests

To test face detection functionality:

```bash
# Run face detection tests with Kaggle dataset
python tests/test_kaggle_face_detection.py
```

**Note:** Testing requires Kaggle API credentials. Place your `kaggle.json` file in `~/.kaggle/` directory.

## Initial test scenarios

1. Detect a humanoid and send an email
