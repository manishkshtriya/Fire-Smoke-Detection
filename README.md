# 🔥 Fire & Smoke Detection System using YOLOv8

> **Real-time AI-powered Fire & Smoke Detection Platform** built using
> **YOLOv8, Flask, OpenCV, PyTorch, SQLAlchemy, and SQLite**.

## Overview

This project provides real-time fire and smoke detection using a
custom-trained YOLOv8 model integrated into a Flask web application with
authentication, alerting, history tracking, reporting, and configurable
settings.

## Features

-   Real-time webcam detection
-   YOLOv8 custom-trained model
-   Flask dashboard
-   Login authentication
-   SQLite database
-   Detection history
-   Reports
-   Email alerts
-   Alarm notifications
-   Screenshot storage

## Technology Stack

-   Python 3.11
-   Flask
-   SQLAlchemy
-   OpenCV
-   PyTorch
-   Ultralytics YOLOv8
-   SQLite
-   Bootstrap 5

## Dataset

         Split     Images
  ------------ ----------
         Train       5783
    Validation       1630
          Test        817
     **Total**   **8230**

## Training

-   Base Model: YOLOv8 Nano
-   Epochs: 100
-   Batch Size: 16
-   Image Size: 640
-   Optimizer: AdamW
-   Early Stopping: 20

## Installation

``` bash
git clone https://github.com/badivana/Fire-Smoke-Detection.git
cd Fire-and-Smoke-Detection

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

python run.py
```

## Environment Variables

``` env

ALERT_EMAIL=your_email@gmail.com
ALERT_EMAIL_PASS=your_app_password

```

## Future Improvements

-   Docker
-   Kubernetes
-   ONNX Export
-   TensorRT
-   RTSP Cameras
-   Cloud Deployment

## License

MIT License

## Author

**Prajwal B T**

GitHub: https://github.com/badivana LinkedIn:
https://linkedin.com/in/prajwalbadivana
