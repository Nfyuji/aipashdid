"""مهام وإلى دو (To-Do) إدارية"""
from datetime import datetime
from models import db


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='pending')   # pending, in_progress, done, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    def get_status_arabic(self):
        return {'pending': 'قيد الانتظار', 'in_progress': 'قيد التنفيذ', 'done': 'منتهية', 'cancelled': 'ملغاة'}.get(self.status, self.status)

    def get_priority_arabic(self):
        return {'low': 'منخفضة', 'medium': 'متوسطة', 'high': 'عالية', 'urgent': 'عاجلة'}.get(self.priority, self.priority)
