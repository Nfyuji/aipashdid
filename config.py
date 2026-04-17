import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'phishdetector-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///phishdetector.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
