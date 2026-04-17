"""قوالب رسائل النظام والتحذيرات"""
from datetime import datetime
from models import db


class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)  # e.g. warning_high_risk, system_maintenance
    subject = db.Column(db.String(300), default='')
    body_html = db.Column(db.Text, default='')
    body_text = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
