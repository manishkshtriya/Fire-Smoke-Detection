import cv2
import time
from datetime import datetime
from pathlib import Path
import numpy as np
from ultralytics import settings
import threading

from .. import db
from ..models import Alert, Camera, Detection, Settings
from YOLOv8LiveCam import send_email, play_alert_sound

_detector = None
_detector_key = None
_last_logged = {}



def _normalize_source(source):
    if source is None:
        return 0
    if isinstance(source, (int, float)):
        return int(source)
    if isinstance(source, str):
        text = source.strip()
        if not text:
            return 0
        try:
            return int(text)
        except ValueError:
            return text
    return source


class FallbackCameraDetector:
    """Simple camera stream fallback used when the YOLO model cannot be loaded."""

    def __init__(self, source=0):
        self.source = _normalize_source(source)
        self.capture = None
        candidates = []
        if isinstance(self.source, str):
            candidates.append(self.source)
        else:
            candidates.append(self.source)
            candidates.extend([0, 1, 2])
        for candidate in candidates:
            cap = cv2.VideoCapture(candidate)
            if cap.isOpened():
                self.capture = cap
                self.source = candidate
                return
            try:
                cap.release()
            except Exception:
                pass
        raise RuntimeError('Could not open video source')

    def read_frame(self):
        return self.capture.read()

    def process_frame(self, frame, conf=0.5):
        
        meta = {
            'fire': False,
            'smoke': False,
            'filtered_count': 0,
            'detection_duration_fire': 0,
            'detection_duration_smoke': 0,
        }
        return _draw_status_overlay(frame, meta, []), meta, []

    def save_snapshot(self, annotated_frame, prefix='detection'):
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        Path('screenshots').mkdir(exist_ok=True)
        path = Path('screenshots') / f"{prefix}_{timestamp}.jpg"
        cv2.imwrite(str(path), annotated_frame)
        return str(path)

    def release(self):
        try:
            self.capture.release()
        except Exception:
            pass


def _is_detector_available(detector):
    try:
        capture = getattr(detector, 'capture', None)
        return capture is not None and capture.isOpened()
    except Exception:
        return False


def get_detector(source=0, weights='optimized150.pt'):
    global _detector, _detector_key
    normalized_source = _normalize_source(source)
    key = (normalized_source, weights)
    if _detector is None or _detector_key != key or not _is_detector_available(_detector):
        if _detector is not None:
            try:
                _detector.release()
            except Exception:
                pass
        try:
            from YOLOv8LiveCam import LiveDetector
            _detector = LiveDetector(weights_path=weights, source=normalized_source)
        except Exception as exc:
            import traceback

            traceback.print_exc()

            print("Detector initialization failed:", exc)
            _detector = FallbackCameraDetector(source=normalized_source)
        _detector_key = key
    return _detector


def _get_or_create_camera(name='Default Camera', source='0'):
    camera = Camera.query.filter_by(name=name, source=source).first()
    if camera is None:
        camera = Camera(name=name, source=source, status='online')
        db.session.add(camera)
        db.session.commit()
    return camera


def _persist_detection(class_name, confidence, image_path, camera):
    detection = Detection(
        class_name=class_name,
        confidence=confidence,
        image_path=image_path,
        camera_id=camera.id,
    )
    db.session.add(detection)
    db.session.commit()

    alert = Alert(
        detection_id=detection.id,
        alert_type=class_name.lower(),
        sent_status=False,
    )
    db.session.add(alert)
    db.session.commit()
    return detection


def _should_log(class_name):
    now = datetime.utcnow()
    last = _last_logged.get(class_name.lower())
    if last is None or (now - last).total_seconds() >= 5:
        _last_logged[class_name.lower()] = now
        return True
    return False


def _placeholder_frame(message='Camera unavailable'):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message, (40, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return frame


def _draw_status_overlay(frame, meta, detections):
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


def frame_generator(source=0):
    """Yield MJPEG frames from the detector and persist detections to SQLite."""
    print("FRAME GENERATOR STARTED")
    det = get_detector(source=source)
    camera = None

    settings = Settings.query.first()

    fire_conf = settings.fire_confidence if settings else 0.55
    smoke_conf = settings.smoke_confidence if settings else 0.75
    try:
        while True:
            try:
                print("READING FRAME")
                ret, frame = det.read_frame()
            except Exception:
                ret = False
                frame = None

            if not ret or frame is None:
                frame = _placeholder_frame()
                ret2, jpeg = cv2.imencode('.jpg', frame)
                if ret2:
                    frame_bytes = jpeg.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(0.03)
                continue

            annotated, meta, detections = det.process_frame(
                frame,
                fire_conf=fire_conf,
                smoke_conf=smoke_conf
            )

            if detections and (meta.get('fire') or meta.get('smoke')):
                if camera is None:
                    camera = _get_or_create_camera()
                highest = max(detections, key=lambda item: item['confidence'])
                if _should_log(highest['class_name']):

                    snapshot_path = det.save_snapshot(
                        annotated,
                        prefix=highest['class_name'].lower()
                    )

                    _persist_detection(
                        highest['class_name'],
                        round(highest['confidence'], 2),
                        snapshot_path,
                        camera
                    )

                    # -----------------------------
                    # Play Alarm
                    # -----------------------------
                    try:
                        if settings.alert_sound_enabled:
                            threading.Thread(
                                target=play_alert_sound,
                                daemon=True
                            ).start()
                    except Exception as e:
                        print("Sound Error:", e)

                    # -----------------------------
                    # Send Email (Background Thread)
                    # -----------------------------
                    try:
                        if settings.email_receiver:

                            threading.Thread(
                                target=send_email,
                                kwargs={
                                    "to_email": settings.email_receiver,
                                    "subject": f"🚨 {highest['class_name']} Detected",
                                    "body": (
                                        f"{highest['class_name']} detected.\n\n"
                                        f"Confidence: {highest['confidence']:.2f}\n"
                                        f"Time: {datetime.now()}"
                                    ),
                                    "screenshot_path": f"app/static/{snapshot_path}",
                                },
                                daemon=True
                            ).start()

                    except Exception as e:
                        print("Email Error:", e)

            ret2, jpeg = cv2.imencode('.jpg', annotated)    
            if not ret2:
                continue
            frame_bytes = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)
    finally:
        try:
            det.release()
        except Exception:
            pass


def get_frame_generator(source=None):
    if source is None:
        try:
            settings = Settings.query.first()
            if settings and settings.camera_source:
                source = settings.camera_source
            else:
                source = 0
        except Exception:
            source = 0
    return frame_generator(source=source)
