import os
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # تأكد من تهيئة قاعدة البيانات
    db.init_app(app)

    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # CSRF
    csrf = CSRFProtect()
    csrf.init_app(app)

    # صفحة اختبار فقط
    @app.route('/')
    def home():
        return "🚀 APP IS RUNNING SUCCESSFULLY ON RENDER"

    return app


# مهم لـ gunicorn
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
