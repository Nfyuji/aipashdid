from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_models(app):
    """استيراد كل النماذج حتى تُنشأ الجداول"""
    from models.user import User
    from models.department import Department
    from models.email import AnalyzedEmail
    from models.threat import Threat
    from models.block_list import BlockList
    from models.notification import Notification
