"""تسجيل أحداث السجل (Audit Log)"""
from flask import request
from models import db
from models.audit_log import AuditLog


def log_action(user_id, action, details=''):
    try:
        ip = request.remote_addr if request else ''
        entry = AuditLog(user_id=user_id, action=action, details=details[:2000] if details else '', ip_address=ip)
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
