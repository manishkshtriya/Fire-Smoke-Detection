from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, Response, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import bp
from ..models import Alert, Camera, Detection, Settings, User
from .. import db
from ..services.detector import get_frame_generator

def _ensure_settings():
    settings = Settings.query.first()
    if settings is None:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()
    return settings


def _get_stats():
    total = Detection.query.count()
    today = Detection.query.filter(Detection.timestamp >= datetime.utcnow().date()).count()
    fire_count = Detection.query.filter(Detection.class_name == 'Fire').count()
    smoke_count = Detection.query.filter(Detection.class_name == 'Smoke').count()
    return {
        'total_detections': total,
        'today_detections': today,
        'fire_count': fire_count,
        'smoke_count': smoke_count,
    }


@bp.route('/')
@login_required
def index():
    recent = []
    for item in Detection.query.order_by(Detection.timestamp.desc()).limit(8).all():
        camera_name = 'Unknown'
        if item.camera_id:
            camera = Camera.query.get(item.camera_id)
            if camera:
                camera_name = camera.name
        recent.append({
            'timestamp': item.timestamp,
            'class_name': item.class_name,
            'confidence': item.confidence,
            'camera_name': camera_name,
            'image_path': item.image_path,
        })
    return render_template('dashboard.html', stats=_get_stats(), recent_detections=recent)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))


def mjpeg_response(frame_generator):
    return Response(frame_generator, mimetype='multipart/x-mixed-replace; boundary=frame')


@bp.route('/video_feed')
@login_required
def video_feed():
    source = request.args.get("source")

    app = current_app._get_current_object()

    def generate():
        with app.app_context():
            yield from get_frame_generator(source=source)

    return mjpeg_response(generate())


@bp.route('/history')
@login_required
def history():
    query = request.args.get('q', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 10

    items = Detection.query
    if query:
        items = items.filter(Detection.class_name.ilike(f'%{query}%'))

    pagination = items.order_by(Detection.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    detections = []
    for item in pagination.items:
        camera_name = 'Unknown'
        if item.camera_id:
            camera = Camera.query.get(item.camera_id)
            if camera:
                camera_name = camera.name
        print("DB IMAGE PATH:", item.image_path)
        detections.append({
            'id': item.id,
            'timestamp': item.timestamp,
            'class_name': item.class_name,
            'confidence': item.confidence,
            'camera_name': camera_name,
            'image_path': item.image_path,
        })
    return render_template('history.html', detections=detections, pagination=pagination, query=query)


@bp.route('/reports')
@login_required
def reports():
    detections = Detection.query.all()
    by_day = {}
    for item in detections:
        day = item.timestamp.strftime('%Y-%m-%d') if item.timestamp else 'unknown'
        by_day[day] = by_day.get(day, 0) + 1

    fire_by_day = {}
    smoke_by_day = {}
    for item in detections:
        day = item.timestamp.strftime('%Y-%m-%d') if item.timestamp else 'unknown'
        if item.class_name == 'Fire':
            fire_by_day[day] = fire_by_day.get(day, 0) + 1
        elif item.class_name == 'Smoke':
            smoke_by_day[day] = smoke_by_day.get(day, 0) + 1

    settings = _ensure_settings()

    return render_template('reports.html', reports=by_day, fire_by_day=fire_by_day, smoke_by_day=smoke_by_day, settings=settings)


@bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    settings = _ensure_settings()

    if request.method == 'POST':
        settings.fire_confidence = float(request.form.get('fire_confidence', settings.fire_confidence))
        settings.smoke_confidence = float(request.form.get('smoke_confidence', settings.smoke_confidence))
        settings.detection_duration = int(request.form.get('detection_duration', settings.detection_duration))
        settings.email_receiver = request.form.get('email_receiver', settings.email_receiver)
        settings.alert_sound_enabled = request.form.get('alert_sound_enabled') == 'on'
        settings.camera_source = request.form.get('camera_source', settings.camera_source)
        db.session.commit()
        flash('Settings updated successfully')

    return render_template('settings.html', settings=settings)


@bp.route('/api/detections')
@login_required
def api_detections():
    items = Detection.query.order_by(Detection.timestamp.desc()).limit(20).all()
    return jsonify([{
        'id': item.id,
        'class_name': item.class_name,
        'confidence': item.confidence,
        'timestamp': item.timestamp.isoformat(),
        'image_path': item.image_path,
    } for item in items])


@bp.route('/api/history')
@login_required
def api_history():
    return api_detections()


@bp.route('/api/stats')
@login_required
def api_stats():
    return jsonify(_get_stats())


@bp.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    settings = _ensure_settings()
    payload = request.get_json(silent=True) or {}
    settings.fire_confidence = payload.get('fire_confidence', settings.fire_confidence)
    settings.smoke_confidence = payload.get('smoke_confidence', settings.smoke_confidence)
    settings.detection_duration = payload.get('detection_duration', settings.detection_duration)
    settings.email_receiver = payload.get('email_receiver', settings.email_receiver)
    settings.alert_sound_enabled = payload.get('alert_sound_enabled', settings.alert_sound_enabled)
    settings.camera_source = payload.get('camera_source', settings.camera_source)
    db.session.commit()
    return jsonify({'status': 'ok', 'settings': {
        'fire_confidence': settings.fire_confidence,
        'smoke_confidence': settings.smoke_confidence,
        'detection_duration': settings.detection_duration,
        'email_receiver': settings.email_receiver,
        'alert_sound_enabled': settings.alert_sound_enabled,
        'camera_source': settings.camera_source,
    }})
