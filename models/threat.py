from datetime import datetime
from models import db


class Threat(db.Model):
    """سجل تهديد / حدث أمني"""
    __tablename__ = 'threats'

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('analyzed_emails.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    source_ip = db.Column(db.String(45), default='')
    country_code = db.Column(db.String(10), default='')
    status = db.Column(db.String(20), default='active')    # active, resolved, ignored
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    email = db.relationship('AnalyzedEmail', backref='threats', foreign_keys=[email_id])
    created_by = db.relationship('User', backref='reported_threats', foreign_keys=[created_by_id])

    def get_severity_badge_class(self):
        return {
            'critical': 'badge-danger',
            'high': 'badge-danger',
            'medium': 'badge-warning',
            'low': 'badge-info'
        }.get(self.severity, 'badge-secondary')

    def get_severity_arabic(self):
        return {'critical': 'حرج', 'high': 'عالي', 'medium': 'متوسط', 'low': 'منخفض'}.get(self.severity, '—')

    def __repr__(self):
        return f'<Threat {self.title}>'
