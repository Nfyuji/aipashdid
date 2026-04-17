import os
from flask import Flask, redirect, url_for, render_template, request
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )

    # Load config
    app.config.from_object(Config)

    # ---------------- INIT EXTENSIONS ----------------
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    csrf = CSRFProtect()
    csrf.init_app(app)

    # ---------------- USER LOADER ----------------
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except:
            return None

    # ---------------- BLUEPRINTS ----------------
    try:
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

    except Exception as e:
        print("Blueprint import error:", e)

    # ---------------- MAINTENANCE ----------------
    @app.before_request
    def maintenance_guard():
        try:
            from models.system_settings import SystemSettings

            maintenance_mode = SystemSettings.get("maintenance_mode", "0")

            if maintenance_mode != "1":
                return None

            if request.endpoint in (None, "static", "maintenance_page"):
                return None

            if request.endpoint and request.endpoint.startswith("auth."):
                return None

            if getattr(current_user, "is_authenticated", False) and getattr(current_user, "role", "") == "admin":
                return None

            return redirect(url_for("maintenance_page"))

        except:
            return None

    # ---------------- ROUTES ----------------

    @app.route("/")
    def home():
        return redirect(url_for("auth.landing"))

    @app.route("/maintenance")
    def maintenance_page():
        return render_template("maintenance.html")

    @app.route("/test")
    def test():
        return "APP IS RUNNING OK 🚀"

    # ---------------- DB INIT SAFE ----------------
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print("DB error:", e)

    return app


# ---------------- RENDER ENTRY ----------------
app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
