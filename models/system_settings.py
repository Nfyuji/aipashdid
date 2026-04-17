"""إعدادات النظام (مفتاح-قيمة)"""
from models import db


class SystemSettings(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default='')
    description = db.Column(db.String(255), default='')

    @staticmethod
    def get(key, default=None):
        s = SystemSettings.query.filter_by(key=key).first()
        return s.value if s else default

    @staticmethod
    def set(key, value, description=''):
        s = SystemSettings.query.filter_by(key=key).first()
        if s:
            s.value = str(value)
            if description:
                s.description = description
        else:
            s = SystemSettings(key=key, value=str(value), description=description)
            db.session.add(s)
        db.session.commit()
        return s
