try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

from fileinput import filename
from pathlib import Path
from sys import prefix

import cv2
try:
    import pygame
except Exception:
    pygame = None
import time
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize pygame mixer for sound playback
if pygame is not None:
    try:
        pygame.mixer.init()
    except Exception:
        # In headless environments pygame may fail to init; keep going
        pass


# Email sending function
def send_email(to_email, subject, body, screenshot_path):
    """Send an email with attachment using credentials from environment variables."""
    your_email = os.environ.get('ALERT_EMAIL')
    your_password = os.environ.get('ALERT_EMAIL_PASS')

    if not your_email or not your_password:
        print("Error: Email credentials not found in environment variables.")
        return

    # Create the email content
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = your_email
    msg['To'] = to_email

    # Attach the screenshot if available
    if screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(screenshot_path)
            msg.add_attachment(file_data, maintype='image', subtype='jpeg', filename=file_name)

    # Establish a connection to the Gmail SMTP server
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(your_email, your_password)
        smtp.send_message(msg)

    print(f"Email sent successfully to {to_email} with screenshot: {screenshot_path}")


# Play the alert sound
def play_alert_sound(sound_path='alert_sound.mp3'):
    if pygame is None:
        return
    try:
        pygame.mixer.music.load(sound_path)  # Ensure you have an alert sound file
        pygame.mixer.music.play()
    except Exception:
        # Sound playback is optional; ignore errors
        pass


def _draw_status_overlay(frame, meta, detections):
    """Draw a readable on-screen status box for the live feed."""
    display_frame = frame.copy()
    status_text = 'Status: No suspicious activity'
    color = (0, 255, 0)

    if meta.get('fire') or meta.get('smoke'):
        labels = []
        if meta.get('fire'):
            labels.append('Fire')
        if meta.get('smoke'):
            labels.append('Smoke')
        status_text = 'Status: ' + ' + '.join(labels)
        color = (0, 0, 255)

    if detections:
        top_detection = detections[0]
        status_text += f" | {top_detection['class_name']} {top_detection['confidence']:.2f}"

    cv2.rectangle(display_frame, (8, 8), (520, 70), (0, 0, 0), -1)
    cv2.putText(display_frame, 'LIVE DATA', (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    cv2.putText(display_frame, status_text, (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return display_frame


class LiveDetector:
    """Wrapper around the existing YOLOv8 detection logic.

    This class preserves the original detection thresholds and logic
    but exposes a simple API that other parts of the application can use.
    """


    def __init__(self, weights_path='optimized150.pt', source=0):

        print("=" * 60)
        print("Creating LiveDetector")
        print("Weights:", weights_path)
        print("Camera Source:", source)

        self.model = YOLO(weights_path)

        self.capture = cv2.VideoCapture(source)

        print("Camera opened:", self.capture.isOpened())

        if not self.capture.isOpened():
            raise RuntimeError("Could not open video source")

        # detection state
        self.detection_duration_fire = 0
        self.detection_duration_smoke = 0
        self.detection_threshold_fire = 2
        self.detection_threshold_smoke = 3
        self.alert_sent_fire = False
        self.alert_sent_smoke = False

    def read_frame(self):
        """Read a frame from the camera and return (success, frame)."""
        return self.capture.read()

    def process_frame(self, frame, fire_conf=0.55, smoke_conf=0.75):
        print("PROCESS FRAME CALLED")
        """Run inference on a single frame and return annotated frame and detection metadata.

        Returns: annotated_frame (ndarray), detections (list of dict)
        """
        results = self.model.predict(source=frame, imgsz=320,  conf=min(fire_conf, smoke_conf), verbose=False, device="cpu")
        detections = results[0].boxes
        fire_detected = False
        smoke_detected = False
        filtered_boxes = []

        print(f"Raw detections count: {len(detections)}")
        for box in detections:
            class_index = int(box.cls)
            confidence = float(box.conf)
            print(f"Detected class={class_index} confidence={confidence:.3f}")
            if class_index == 0 and confidence >= fire_conf:
                fire_detected = True
                filtered_boxes.append(box)
            elif class_index == 1 and confidence >= smoke_conf:
                smoke_detected = True
                filtered_boxes.append(box)

        # update durations
        if fire_detected:
            self.detection_duration_fire += 1 / 30
        else:
            self.detection_duration_fire = 0

        if smoke_detected:
            self.detection_duration_smoke += 1 / 30
        else:
            self.detection_duration_smoke = 0

        # prepare annotated frame with filtered boxes
        annotated_frame = frame.copy()

        for box in filtered_boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            conf = float(box.conf)
            cls = int(box.cls)

            label = "Fire" if cls == 0 else "Smoke"

            color = (0, 0, 255) if cls == 0 else (255, 255, 0)

            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
            annotated_frame,
            f"{label} {conf:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
            )

        # collect metadata
        detection_details = []
        for box in filtered_boxes:
            detection_details.append({
                'class_name': 'Fire' if int(box.cls) == 0 else 'Smoke',
                'confidence': float(box.conf),
            })

        meta = {
            'fire': fire_detected,
            'smoke': smoke_detected,
            'filtered_count': len(filtered_boxes),
            'detection_duration_fire': self.detection_duration_fire,
            'detection_duration_smoke': self.detection_duration_smoke,
        }

        annotated_frame = _draw_status_overlay(annotated_frame, meta, detection_details)
        return annotated_frame, meta, detection_details

    def save_snapshot(self, annotated_frame, prefix="detection"):
        timestamp = time.strftime("%Y%m%d-%H%M%S")

        snapshot_dir = Path("app/static/screenshots")
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{prefix}_{timestamp}.jpg"
        filepath = snapshot_dir / filename

        success = cv2.imwrite(str(filepath), annotated_frame)

        print("=" * 60)
        print("SAVE SNAPSHOT")
        print("Success :", success)
        print("Saved to:", filepath.resolve())
        print("=" * 60)

        if not success:
            raise RuntimeError(f"Failed to save snapshot to {filepath}")

        return f"screenshots/{filename}"

    def release(self):
        try:
            self.capture.release()
        except Exception:
            pass


if __name__ == '__main__':
    # If executed directly, keep original behaviour: open camera and show window
    if YOLO is None:
        raise RuntimeError('ultralytics is not installed. Install requirements before running the detector directly.')
    model = YOLO('optimized150.pt')
    capture = cv2.VideoCapture(0)

    if not capture.isOpened():
        print('Error: Could not open video source.')
        exit()

    detection_duration_fire = 0
    detection_duration_smoke = 0
    detection_threshold_fire = 2
    detection_threshold_smoke = 3
    alert_sent_fire = False
    alert_sent_smoke = False

    while True:
        isTrue, frame = capture.read()
        if isTrue:
            results = model.predict(source=frame, imgsz=640, conf=0.5, show=False)
            detections = results[0].boxes
            fire_detected = False
            smoke_detected = False
            filtered_boxes = []

            for box in detections:
                class_index = int(box.cls)
                confidence = box.conf
                if class_index == 0 and confidence > 0.55:
                    fire_detected = True
                    filtered_boxes.append(box)
                elif class_index == 1 and confidence > 0.75:
                    smoke_detected = True
                    filtered_boxes.append(box)

            if fire_detected:
                detection_duration_fire += 1 / 30
            else:
                detection_duration_fire = 0

            if smoke_detected:
                detection_duration_smoke += 1 / 30
            else:
                detection_duration_smoke = 0

            if detection_duration_fire >= detection_threshold_fire and not alert_sent_fire:
                timestamp = time.strftime('%Y%m%d-%H%M%S')
                screenshot_path = f"./fire_detected_{timestamp}.jpg"
                results[0].boxes = filtered_boxes
                annotated_frame = results[0].plot()
                cv2.imwrite(screenshot_path, annotated_frame)
                play_alert_sound()
                # Fetch receiver email from environment or use a default
                receiver_email = os.environ.get('RECEIVER_EMAIL', 'your_target_email@example.com')
                send_email(receiver_email, 'Fire Detected!', 'Fire has been detected.', screenshot_path)
                alert_sent_fire = True
                print(f'Fire screenshot saved and alert triggered: {screenshot_path}')

            if detection_duration_smoke >= detection_threshold_smoke and not alert_sent_smoke:
                timestamp = time.strftime('%Y%m%d-%H%M%S')
                screenshot_path = f"./smoke_detected_{timestamp}.jpg"
                results[0].boxes = filtered_boxes
                annotated_frame = results[0].plot()
                cv2.imwrite(screenshot_path, annotated_frame)
                play_alert_sound()
                # Fetch receiver email from environment or use a default
                receiver_email = os.environ.get('RECEIVER_EMAIL', 'your_target_email@example.com')
                send_email(receiver_email, 'Smoke Detected!', 'Smoke has been detected.', screenshot_path)
                alert_sent_smoke = True
                print(f'Smoke screenshot saved and alert triggered: {screenshot_path}')

            if detection_duration_fire < detection_threshold_fire:
                alert_sent_fire = False
            if detection_duration_smoke < detection_threshold_smoke:
                alert_sent_smoke = False

            results[0].boxes = filtered_boxes
            annotated_frame = results[0].plot()
            annotated_frame = _draw_status_overlay(
                annotated_frame,
                {
                    'fire': fire_detected,
                    'smoke': smoke_detected,
                    'filtered_count': len(filtered_boxes),
                    'detection_duration_fire': detection_duration_fire,
                    'detection_duration_smoke': detection_duration_smoke,
                },
                [
                    {'class_name': 'Fire', 'confidence': float(box.conf)} for box in filtered_boxes if int(box.cls) == 0
                ] + [
                    {'class_name': 'Smoke', 'confidence': float(box.conf)} for box in filtered_boxes if int(box.cls) == 1
                ],
            )
            cv2.imshow('YOLOv8 Webcam', annotated_frame)

            if cv2.waitKey(5) & 0xFF == ord('d'):
                break
        else:
            break

    capture.release()
    cv2.destroyAllWindows()
