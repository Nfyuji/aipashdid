# Employee Routes - متاح للأدمن والموظف
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.email import AnalyzedEmail
from ai_engine.detector import analyze_email

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


def employee_or_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('admin', 'employee'):
            return redirect(url_for('auth.landing'))
        return f(*args, **kwargs)
    return decorated


def get_my_emails():
    """الرسائل التي حللها المستخدم الحالي (أو الكل للأدمن)"""
    if current_user.role == 'admin':
        return AnalyzedEmail.query.order_by(AnalyzedEmail.created_at.desc())
    return AnalyzedEmail.query.filter_by(analyzed_by_id=current_user.id).order_by(AnalyzedEmail.created_at.desc())


@employee_bp.route('/')
@login_required
@employee_or_admin_required
def index():
    return redirect(url_for('employee.dashboard'))


@employee_bp.route('/dashboard')
@login_required
@employee_or_admin_required
def dashboard():
    total = get_my_emails().count()
    high_risk = get_my_emails().filter(AnalyzedEmail.risk_level == 'high').count()
    recent = get_my_emails().limit(5).all()
    return render_template('employee/dashboard.html', total=total, high_risk=high_risk, recent=recent)


@employee_bp.route('/inbox')
@login_required
@employee_or_admin_required
def inbox():
    emails = get_my_emails().limit(50).all()
    total = get_my_emails().count()
    high_count = get_my_emails().filter(AnalyzedEmail.risk_level == 'high').count()
    return render_template('employee/inbox.html', emails=emails, total=total, high_count=high_count)


@employee_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
@employee_or_admin_required
def analyze():
    if request.method == 'POST':
        sender = request.form.get('sender_email', '').strip()
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not sender or not subject:
            flash('المرسل والموضوع مطلوبان', 'error')
            return redirect(url_for('employee.analyze'))
        result = analyze_email(sender, subject, body)
        rec = AnalyzedEmail(
            sender_email=sender,
            subject=subject,
            body=body,
            risk_score=result['risk_score'],
            risk_level=result['risk_level'],
            classification=result.get('classification', 'legitimate'),
            reasons=result['reasons'],
            model_used=result.get('model_used', 'rules'),
            status='pending',
            analyzed_by_id=current_user.id
        )
        db.session.add(rec)
        db.session.commit()
        from utils.audit import log_action
        log_action(current_user.id, 'analyze_email', f'email_id={rec.id} risk={rec.risk_level}')
        if rec.risk_level == 'high':
            from models.system_settings import SystemSettings
            if SystemSettings.get('notify_high_risk', '0') == '1':
                from models.notification import Notification
                from models.user import User
                admins = User.query.filter_by(role='admin').all()
                for admin in admins:
                    n = Notification(
                        user_id=admin.id,
                        title='رسالة عالية الخطورة',
                        message=f'تم تحليل رسالة من {sender}: {subject[:50]}',
                        link=f'/admin/analysis-log',
                        is_read=False
                    )
                    db.session.add(n)
                db.session.commit()
                # Optional: email (if SMTP configured)
                try:
                    from utils.mail import send_high_risk_alert
                    for admin in admins:
                        send_high_risk_alert(
                            admin.email,
                            f'High risk email detected:\nFrom: {sender}\nSubject: {subject}\nEmail ID: {rec.id}\nRisk Score: {rec.risk_score}\n\nOpen: /admin/analysis-log'
                        )
                except Exception:
                    pass
        flash('تم تحليل الرسالة بنجاح', 'success')
        return redirect(url_for('employee.result', id=rec.id))
    return render_template('employee/analyze.html')


@employee_bp.route('/my-log')
@login_required
@employee_or_admin_required
def my_log():
    emails = get_my_emails().limit(50).all()
    total = get_my_emails().count()
    high_count = get_my_emails().filter(AnalyzedEmail.risk_level == 'high').count()
    return render_template('employee/my_log.html', emails=emails, total=total, high_count=high_count)


@employee_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@employee_or_admin_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if full_name:
            current_user.full_name = full_name
        new_password = request.form.get('new_password', '')
        if new_password and len(new_password) >= 6:
            current_user.set_password(new_password)
        db.session.commit()
        flash('تم تحديث الملف الشخصي', 'success')
        return redirect(url_for('employee.profile'))
    return render_template('employee/profile.html')


@employee_bp.route('/result')
@login_required
@employee_or_admin_required
def result():
    email_id = request.args.get('id', type=int)
    if email_id:
        em = AnalyzedEmail.query.get(email_id)
        if em and (current_user.role == 'admin' or em.analyzed_by_id == current_user.id):
            return render_template('employee/result.html', email=em, model_used_display=getattr(em, 'model_used', 'rules'))
    em = get_my_emails().first()
    return render_template('employee/result.html', email=em, model_used_display=getattr(em, 'model_used', 'rules') if em else 'rules')
