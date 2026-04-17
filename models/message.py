"""رسائل داخلية بين المستخدمين"""
from datetime import datetime
from models import db


class InternalMessage(db.Model):
    __tablename__ = 'internal_messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null = broadcast to all or role
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, default='')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
