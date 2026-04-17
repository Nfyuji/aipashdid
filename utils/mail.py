# -*- coding: utf-8 -*-
"""إرسال البريد. إذا لم يكن SMTP مُعداً، استدعاء send_password_reset_email يرفع استثناء فيُعرض الرابط في الصفحة."""
from flask import current_app


def send_password_reset_email(to_email, reset_url):
    """إرسال بريد إعادة تعيين كلمة المرور. يرفع إذا البريد غير مُعد."""
    mail = getattr(current_app, 'extensions', {}).get('mail')
    if not mail:
        raise RuntimeError('Mail not configured')
    from flask_mail import Message
    msg = Message(
        subject='إعادة تعيين كلمة المرور - PhishDetector',
        recipients=[to_email],
        body=f'لإعادة تعيين كلمة المرور استخدم الرابط التالي (صالح لمدة ساعتين):\n{reset_url}',
        charset='utf-8'
    )
    mail.send(msg)


def send_high_risk_alert(to_email, text):
    """تنبيه بريد عند رسالة عالية الخطورة (اختياري)."""
    mail = getattr(current_app, 'extensions', {}).get('mail')
    if not mail:
        raise RuntimeError('Mail not configured')
    from flask_mail import Message
    msg = Message(
        subject='تنبيه أمني: رسالة عالية الخطورة - PhishDetector',
        recipients=[to_email],
        body=str(text),
        charset='utf-8'
    )
    mail.send(msg)
