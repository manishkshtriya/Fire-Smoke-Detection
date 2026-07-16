import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


def create_app(config_object='config.Config'):
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(project_root / 'templates'),
        static_folder=str(project_root / 'app' / 'static'),
    )
    app.config.from_object(config_object)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # register blueprints
    from .routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        os.makedirs(project_root / 'database', exist_ok=True)
        db.create_all()

        from .models import Settings, User

        if Settings.query.first() is None:
            db.session.add(Settings())

        admin_username = os.environ.get('ADMIN_USER') or 'admin'
        admin_email = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
        admin_pass = os.environ.get('ADMIN_PASS') or 'admin123'
        if not User.query.filter_by(username=admin_username).first():
            user = User(username=admin_username, email=admin_email)
            user.set_password(admin_pass)
            db.session.add(user)

        db.session.commit()

    return app
