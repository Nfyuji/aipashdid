from datetime import datetime
from models import db


class BlockList(db.Model):
    """قائمة حظر: بريد، نطاق، أو رابط"""
    __tablename__ = 'block_lists'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(500), nullable=False)     # البريد أو النطاق أو الرابط
    list_type = db.Column(db.String(20), nullable=False)   # email, domain, url
    reason = db.Column(db.String(300), default='')
    added_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    added_by = db.relationship('User', backref='block_list_entries', foreign_keys=[added_by_id])

    def get_type_arabic(self):
        return {'email': 'بريد', 'domain': 'نطاق', 'url': 'رابط'}.get(self.list_type, self.list_type)

    def __repr__(self):
        return f'<BlockList {self.list_type}:{self.value}>'
