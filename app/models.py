from datetime import datetime
from zoneinfo import ZoneInfo
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    source = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(64), default='unknown')


class Detection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String(64))
    confidence = db.Column(db.Float)
    image_path = db.Column(db.String(256))
    timestamp = db.Column(
    db.DateTime,default=lambda: datetime.now(ZoneInfo("Asia/Kolkata"))
)
    camera_id = db.Column(db.Integer, db.ForeignKey('camera.id'))


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, db.ForeignKey('detection.id'))
    alert_type = db.Column(db.String(64))
    sent_status = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fire_confidence = db.Column(db.Float, default=0.55)
    smoke_confidence = db.Column(db.Float, default=0.75)
    detection_duration = db.Column(db.Integer, default=2)
    email_receiver = db.Column(db.String(120), default='admin@example.com')
    alert_sound_enabled = db.Column(db.Boolean, default=True)
    camera_source = db.Column(db.String(256), default='0')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
