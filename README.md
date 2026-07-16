# 🔥 Fire & Smoke Detection System using YOLOv8

> A real-time AI-powered Fire & Smoke Detection System built using
> **YOLOv8**, **PyTorch**, **OpenCV**, and **Flask**.

## Overview

This project implements an end-to-end fire and smoke detection pipeline:

-   Dataset collection and preprocessing
-   Transfer learning using YOLOv8 pretrained on COCO
-   Fine-tuning on a custom Fire & Smoke dataset
-   Real-time webcam detection
-   Flask-based monitoring dashboard
-   SQLite database logging
-   Snapshot storage
-   Email and sound alerts
-   Detection history and reports

------------------------------------------------------------------------

## Features

-   Real-time fire and smoke detection
-   YOLOv8 Nano custom-trained model
-   Live MJPEG video streaming
-   Bounding boxes with confidence scores
-   Detection history
-   Automatic snapshot saving
-   SQLite database
-   Email alerts with image attachment
-   Sound alerts
-   Searchable history
-   Reports page
-   Configurable confidence thresholds
-   Login authentication

------------------------------------------------------------------------

## Technology Stack

-   Python 3.11
-   Flask
-   Flask-SQLAlchemy
-   Flask-Login
-   Flask-Migrate
-   Ultralytics YOLOv8
-   PyTorch
-   OpenCV
-   SQLite
-   Bootstrap 5
-   Pygame
-   python-dotenv

------------------------------------------------------------------------

## Dataset

Original Dataset Classes

-   Fire
-   Flame
-   Smoke

Converted Deployment Classes

-   Fire (Fire + Flame)
-   Smoke

Dataset Statistics

         Split     Images
  ------------ ----------
         Train       5783
    Validation       1630
          Test        817
     **Total**   **8230**

------------------------------------------------------------------------

## Model Training

Training Platform

-   Google Colab
-   Tesla T4 GPU

Base Model

-   YOLOv8 Nano (`yolov8n.pt`)

Transfer Learning

The model was fine-tuned from COCO pretrained weights on the custom Fire
& Smoke dataset.

Training Parameters

  Parameter        Value
  ---------------- -------
  Epochs           100
  Batch Size       16
  Image Size       640
  Optimizer        AdamW
  Learning Rate    0.001
  Early Stopping   20

------------------------------------------------------------------------

## Model Evaluation

Replace these with your final values after training.

  Metric         Value
  -------------- -------
  Precision      --
  Recall         --
  F1 Score       --
  mAP@0.5        --
  mAP@0.5:0.95   --

YOLO automatically generates:

-   results.png
-   confusion_matrix.png
-   PR_curve.png
-   P_curve.png
-   R_curve.png
-   F1_curve.png

------------------------------------------------------------------------

## Project Structure

``` text
Fire-and-Smoke-Detection/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── models.py
│   └── __init__.py
├── templates/
├── database/
├── app/static/
│   └── screenshots/
├── training/
│   └── FireSmoke_Training.ipynb
├── optimized150.pt
├── YOLOv8LiveCam.py
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

------------------------------------------------------------------------

## Installation

``` bash
git clone <repository-url>
cd Fire-and-Smoke-Detection
python -m venv .venv
```

Windows

``` bash
.venv\Scripts\activate
```

Linux/macOS

``` bash
source .venv/bin/activate
```

Install dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Environment Variables

Create a `.env` file.

``` env
SECRET_KEY=your_secret_key
ALERT_EMAIL=your_email@gmail.com
ALERT_EMAIL_PASS=your_app_password
RECEIVER_EMAIL=receiver@gmail.com

ADMIN_USER=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASS=admin123
```

------------------------------------------------------------------------

## Run

``` bash
python run.py
```

Open

    http://127.0.0.1:5000

Default Login

-   Username: admin
-   Password: admin123

------------------------------------------------------------------------

## Dashboard

-   Live Camera Feed
-   Detection Status
-   Bounding Boxes
-   Confidence Score
-   Recent Detections
-   Statistics

------------------------------------------------------------------------

## History

-   Search
-   Pagination
-   Detection Time
-   Confidence
-   Camera
-   Snapshot Viewer

------------------------------------------------------------------------

## Reports

-   Daily Detection Count
-   Fire Statistics
-   Smoke Statistics
-   Detection Trends

------------------------------------------------------------------------

## Settings

-   Fire Confidence Threshold
-   Smoke Confidence Threshold
-   Detection Duration
-   Camera Source
-   Email Receiver
-   Alert Sound

------------------------------------------------------------------------

## Database

### users

Stores login credentials.

### settings

Stores system configuration.

### cameras

Stores camera information.

### detections

-   Detection Type
-   Confidence
-   Timestamp
-   Snapshot Path

### alerts

Stores alert status.

------------------------------------------------------------------------

## API Endpoints

-   /
-   /login
-   /logout
-   /video_feed
-   /history
-   /reports
-   /settings
-   /api/stats
-   /api/history
-   /api/detections
-   /api/settings

------------------------------------------------------------------------

## Screenshots

Detection snapshots are automatically saved to:

    app/static/screenshots/

------------------------------------------------------------------------

## Alerts

### Email

-   Detection Type
-   Confidence
-   Timestamp
-   Attached Snapshot

### Sound

Pygame plays an alert sound whenever fire or smoke is detected.

------------------------------------------------------------------------

## Troubleshooting

### Camera

Try changing:

``` python
cv2.VideoCapture(0)
```

to

``` python
cv2.VideoCapture(1)
```

or

``` python
cv2.VideoCapture(2)
```

### Model

Ensure the trained model exists in the project root.

### Email

Verify:

-   Gmail App Password
-   Internet Connection
-   SMTP Credentials

------------------------------------------------------------------------

## Model Training

The YOLOv8 model used in this project was trained in Google Colab.

Training notebook:

```
notebooks/training1.ipynb
```

The notebook includes:

- Dataset download from Roboflow
- Dataset verification
- YOLOv8 model selection
- Training configuration
- Hyperparameters
- Validation
- Exporting the final model (`optimized150.pt`)

----------------------------------------------------------

## Future Improvements

-   IP Camera Support
-   RTSP Streams
-   Multiple Cameras
-   SMS Alerts
-   WhatsApp Alerts
-   Docker Deployment
-   Cloud Deployment
-   Mobile Application
-   ONNX Export
-   TensorRT Optimization
-   Analytics Dashboard

------------------------------------------------------------------------

## References

-   Ultralytics YOLOv8
-   PyTorch
-   OpenCV
-   Flask
-   Roboflow
-   SQLite

------------------------------------------------------------------------

## License

MIT License

------------------------------------------------------------------------

## Author

Developed as a final-year engineering project demonstrating transfer
learning, computer vision, and real-time fire & smoke detection using
YOLOv8.
