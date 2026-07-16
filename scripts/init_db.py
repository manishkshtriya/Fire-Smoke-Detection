import os
from app import create_app, db
from app.models import User


def init_db():
    app = create_app()
    with app.app_context():
        os.makedirs('database', exist_ok=True)
        db.create_all()

        admin_username = os.environ.get('ADMIN_USER') or 'admin'
        admin_email = os.environ.get('ADMIN_EMAIL') or 'admin@example.com'
        admin_pass = os.environ.get('ADMIN_PASS') or 'admin123'

        if not User.query.filter_by(username=admin_username).first():
            u = User(username=admin_username, email=admin_email)
            u.set_password(admin_pass)
            db.session.add(u)
            db.session.commit()
            print(f'Created admin user: {admin_username} / {admin_pass} (change password after first login)')
        else:
            print('Admin user already exists')


if __name__ == '__main__':
    init_db()
