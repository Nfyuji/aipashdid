from datetime import datetime
from models import db


class AnalyzedEmail(db.Model):
    """رسالة تم تحليلها (صندوق الوارد / التحليل)"""
    __tablename__ = 'analyzed_emails'

    id = db.Column(db.Integer, primary_key=True)
    sender_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, default='')
    risk_level = db.Column(db.String(20), default='low')   # low, medium, high
    risk_score = db.Column(db.Integer, default=0)          # 0-100
    classification = db.Column(db.String(20), default='legitimate')  # legitimate, spam, phishing
    reasons = db.Column(db.Text, default='')               # تفسير التصنيف (Explainable AI)
    model_used = db.Column(db.String(20), default='rules')  # rules | ml (أي نموذج استُخدم)
    status = db.Column(db.String(20), default='pending')   # pending, reviewed, blocked
    analyzed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyzed_by = db.relationship('User', backref='analyzed_emails', foreign_keys=[analyzed_by_id])

    def get_risk_badge_class(self):
        if self.risk_level == 'high':
            return 'badge-danger'
        if self.risk_level == 'medium':
            return 'badge-warning'
        return 'badge-success'

    def get_risk_arabic(self):
        return {'high': 'عالي', 'medium': 'متوسط', 'low': 'منخفض'}.get(self.risk_level, 'منخفض')

    def get_classification_arabic(self):
        return {'legitimate': 'عادي', 'spam': 'مزعج', 'phishing': 'احتيالي'}.get(self.classification or 'legitimate', 'عادي')

    def __repr__(self):
        return f'<AnalyzedEmail {self.subject[:30]}>'
