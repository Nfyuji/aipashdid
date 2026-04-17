import os
from flask import Flask, redirect, url_for, request, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db
from models.user import User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure instance folder exists
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'يرجى تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'warning'

    csrf = CSRFProtect()
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.security import security_bp
    from routes.manager import manager_bp
    from routes.employee import employee_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)

    # Maintenance mode (blocks non-admin)
    @app.before_request
    def maintenance_guard():
        try:
            from flask_login import current_user
            from models.system_settings import SystemSettings
            maintenance_mode = SystemSettings.get('maintenance_mode', '0')
            if maintenance_mode != '1':
                return None

            # allow static + auth endpoints + maintenance page itself
            if request.endpoint in (None, 'static', 'maintenance_page'):
                return None
            if request.endpoint and request.endpoint.startswith('auth.'):
                return None

            # allow admins
            if getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'role', '') == 'admin':
                return None

            return redirect(url_for('maintenance_page'))
        except Exception:
            return None

    @app.route('/maintenance')
    def maintenance_page():
        return render_template('maintenance.html')

    # Landing page route
    @app.route('/')
    def landing():
        return redirect(url_for('auth.landing'))

    # Import all models so tables are created
    from models.user import User
    from models.department import Department
    from models.email import AnalyzedEmail
    from models.threat import Threat
    from models.block_list import BlockList
    from models.notification import Notification
    from models.audit_log import AuditLog
    from models.system_settings import SystemSettings
    from models.message import InternalMessage
    from models.task import Task
    from models.email_template import EmailTemplate
    from models.password_reset import PasswordResetToken

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
