# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from secrets import token_urlsafe
from models import db


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='password_reset_tokens', foreign_keys=[user_id])

    @staticmethod
    def create_for_user(user, expires_hours=2):
        token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        rec = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
        db.session.add(rec)
        db.session.commit()
        return token

    @staticmethod
    def get_user_by_token(token):
        if not token:
            return None
        rec = PasswordResetToken.query.filter_by(token=token).first()
        if not rec or rec.expires_at < datetime.utcnow():
            return None
        return rec.user

    @staticmethod
    def invalidate(token):
        rec = PasswordResetToken.query.filter_by(token=token).first()
        if rec:
            db.session.delete(rec)
            db.session.commit()
