# Admin - لوحة تحكم شاملة لكل المزايا
import os
import io
import csv
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.department import Department
from models.email import AnalyzedEmail
from models.threat import Threat
from models.block_list import BlockList
from models.notification import Notification
from models.audit_log import AuditLog
from models.system_settings import SystemSettings
from models.message import InternalMessage
from models.task import Task
from models.email_template import EmailTemplate
from utils.audit import log_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role != 'admin':
            return redirect(url_for('auth.landing'))
        return f(*args, **kwargs)
    return decorated


# ----- 1) لوحة التحكم الرئيسية -----
@admin_bp.route('/')
@login_required
@admin_required
def index():
    return redirect(url_for('admin.org_dashboard'))


@admin_bp.route('/dashboard')
@login_required
@admin_required
def org_dashboard():
    total_emails = AnalyzedEmail.query.count()
    total_threats = Threat.query.count()
    total_users = User.query.count()
    high_risk = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'high').count()
    pending = AnalyzedEmail.query.filter(AnalyzedEmail.status == 'pending').count()
    active_threats = Threat.query.filter(Threat.status == 'active').count()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return render_template('admin/org_dashboard.html',
        total_emails=total_emails,
        total_threats=total_threats,
        total_users=total_users,
        high_risk=high_risk,
        pending=pending,
        active_threats=active_threats,
        unread_notifications=unread_notifications
    )


# ----- 2) إدارة المستخدمين وصلاحياتهم -----
@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users_manage():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id', type=int)
        user = User.query.get(user_id) if user_id else None
        if action == 'role' and user and user.id != current_user.id:
            new_role = request.form.get('role', '').strip()
            if new_role in ('admin', 'security', 'manager', 'employee'):
                old_role = user.role
                user.role = new_role
                db.session.commit()
                log_action(current_user.id, 'role_change', f'user_id={user_id} {old_role}->{new_role}')
                flash('تم تحديث الدور بنجاح', 'success')
        elif action == 'toggle_active' and user and user.id != current_user.id:
            user.is_active = not user.is_active
            db.session.commit()
            log_action(current_user.id, 'user_toggle_active', f'user_id={user_id} is_active={user.is_active}')
            flash('تم تحديث حالة الحساب', 'success')
        elif action == 'reset_password' and user:
            new_pass = request.form.get('new_password', '')
            if len(new_pass) >= 6:
                user.set_password(new_pass)
                db.session.commit()
                log_action(current_user.id, 'password_reset', f'user_id={user_id}')
                flash('تم تعيين كلمة المرور الجديدة', 'success')
            else:
                flash('كلمة المرور 6 أحرف على الأقل', 'error')
        return redirect(url_for('admin.users_manage'))
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()
    return render_template('admin/users_manage.html', users=users, departments=departments)


@admin_bp.route('/user-permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def user_permissions():
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        new_role = request.form.get('role', '').strip()
        if user_id and new_role in ('admin', 'security', 'manager', 'employee'):
            user = User.query.get(user_id)
            if user and user.id != current_user.id:
                user.role = new_role
                db.session.commit()
                log_action(current_user.id, 'role_change', f'user_id={user_id}')
                flash('تم تحديث دور المستخدم بنجاح', 'success')
            else:
                flash('لا يمكن تعديل هذا المستخدم', 'error')
        else:
            flash('بيانات غير صالحة', 'error')
        return redirect(url_for('admin.user_permissions'))
    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()
    return render_template('admin/user_permissions.html', users=users, departments=departments)


@admin_bp.route('/audit-log')
@login_required
@admin_required
def audit_log():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    q = AuditLog.query.order_by(AuditLog.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page)
    return render_template('admin/audit_log.html', pagination=pagination)


@admin_bp.route('/users/export')
@login_required
@admin_required
def users_export():
    users = User.query.order_by(User.id).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['id', 'username', 'email', 'full_name', 'role', 'department', 'is_active', 'created_at'])
    for u in users:
        w.writerow([u.id, u.username, u.email, u.full_name, u.role, u.department, u.is_active, u.created_at.isoformat() if u.created_at else ''])
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    )


@admin_bp.route('/users/import', methods=['GET', 'POST'])
@login_required
@admin_required
def users_import():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        if f.filename and f.filename.endswith('.csv'):
            stream = io.StringIO(f.stream.read().decode('utf-8-sig'))
            r = csv.DictReader(stream)
            count = 0
            for row in r:
                username = (row.get('username') or '').strip()
                if not username or User.query.filter_by(username=username).first():
                    continue
                email = (row.get('email') or '').strip()
                if not email or User.query.filter_by(email=email).first():
                    continue
                user = User(
                    username=username,
                    email=email,
                    full_name=(row.get('full_name') or username).strip(),
                    role=(row.get('role') or 'employee').strip() or 'employee',
                    department=(row.get('department') or 'عام').strip(),
                    is_active=(row.get('is_active', 'true').strip().lower() == 'true')
                )
                user.set_password(row.get('password', 'ChangeMe123'))
                db.session.add(user)
                count += 1
            db.session.commit()
            log_action(current_user.id, 'users_import', f'count={count}')
            flash(f'تم استيراد {count} مستخدم', 'success')
        else:
            flash('يرجى رفع ملف CSV', 'error')
        return redirect(url_for('admin.users_manage'))
    return render_template('admin/users_import.html')


# ----- 3) الإحصائيات والتقارير -----
@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    total_emails = AnalyzedEmail.query.count()
    low_count = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'low').count()
    medium_count = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'medium').count()
    high_count = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'high').count()
    by_status = {}
    for row in db.session.query(AnalyzedEmail.status, db.func.count(AnalyzedEmail.id)).group_by(AnalyzedEmail.status).all():
        by_status[row[0]] = row[1]
    users_by_role = {}
    for row in db.session.query(User.role, db.func.count(User.id)).group_by(User.role).all():
        users_by_role[row[0]] = row[1]
    by_department = {}
    for row in db.session.query(User.department, db.func.count(User.id)).group_by(User.department).all():
        by_department[row[0] or '—'] = row[1]
    return render_template('admin/statistics.html',
        total_emails=total_emails,
        low_count=low_count,
        medium_count=medium_count,
        high_count=high_count,
        by_status=by_status,
        users_by_role=users_by_role,
        by_department=by_department
    )


@admin_bp.route('/risk-report')
@login_required
@admin_required
def risk_report():
    threats = Threat.query.order_by(Threat.created_at.desc()).limit(100).all()
    high_emails = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'high').order_by(AnalyzedEmail.created_at.desc()).limit(50).all()
    return render_template('admin/risk_report.html', threats=threats, high_emails=high_emails)


@admin_bp.route('/reports/export')
@login_required
@admin_required
def reports_export():
    fmt = request.args.get('format', 'csv')
    if fmt == 'csv':
        emails = AnalyzedEmail.query.order_by(AnalyzedEmail.created_at.desc()).limit(500).all()
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(['id', 'sender', 'subject', 'risk_level', 'risk_score', 'status', 'created_at'])
        for e in emails:
            w.writerow([e.id, e.sender_email, e.subject[:100], e.risk_level, e.risk_score, e.status, e.created_at.isoformat() if e.created_at else ''])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'report_emails_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
        )
    if fmt == 'xlsx':
        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = 'الرسائل'
            ws.append(['id', 'المرسل', 'الموضوع', 'الخطورة', 'النقاط', 'الحالة', 'التاريخ'])
            for e in AnalyzedEmail.query.order_by(AnalyzedEmail.created_at.desc()).limit(500).all():
                ws.append([e.id, e.sender_email, (e.subject or '')[:100], e.risk_level, e.risk_score, e.status, e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else ''])
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True, download_name=f'report_emails_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx')
        except Exception as ex:
            flash(f'خطأ في التصدير: {ex}', 'error')
    if fmt == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

            emails = AnalyzedEmail.query.order_by(AnalyzedEmail.created_at.desc()).limit(200).all()
            buf = io.BytesIO()
            doc = SimpleDocTemplate(buf, pagesize=A4, title='PhishDetector Report')

            styles = getSampleStyleSheet()
            story = []
            story.append(Paragraph('PhishDetector - Email Report (Last 200)', styles['Title']))
            story.append(Paragraph(datetime.now().strftime('%Y-%m-%d %H:%M'), styles['Normal']))
            story.append(Spacer(1, 12))

            data = [['ID', 'Sender', 'Subject', 'Risk', 'Score', 'Status', 'Date']]
            for e in emails:
                data.append([
                    str(e.id),
                    (e.sender_email or '')[:35],
                    (e.subject or '')[:40],
                    (e.risk_level or ''),
                    str(getattr(e, 'risk_score', '')),
                    (e.status or ''),
                    e.created_at.strftime('%Y-%m-%d %H:%M') if e.created_at else ''
                ])

            tbl = Table(data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))

            story.append(tbl)
            doc.build(story)
            buf.seek(0)
            return send_file(
                buf,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'report_emails_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
            )
        except Exception as ex:
            flash(f'خطأ في التصدير PDF: {ex}', 'error')
    return redirect(url_for('admin.statistics'))


@admin_bp.route('/pending')
@login_required
@admin_required
def pending_messages():
    items = AnalyzedEmail.query.filter(AnalyzedEmail.status == 'pending').order_by(AnalyzedEmail.created_at.desc()).limit(100).all()
    return render_template('admin/pending_messages.html', items=items)


# ----- 4) إعدادات النظام والنسخ الاحتياطي والقوالب -----
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def system_settings():
    if request.method == 'POST':
        SystemSettings.set('password_min_length', request.form.get('password_min_length', '6'), 'أقل طول لكلمة المرور')
        SystemSettings.set('notify_high_risk', request.form.get('notify_high_risk', '0'), 'إشعار عند رسالة عالية الخطورة')
        SystemSettings.set('maintenance_mode', request.form.get('maintenance_mode', '0'), 'وضع الصيانة')
        SystemSettings.set('system_version', request.form.get('system_version', '1.0'), 'إصدار النظام')
        log_action(current_user.id, 'settings_update', 'system_settings')
        flash('تم حفظ الإعدادات', 'success')
        return redirect(url_for('admin.system_settings'))
    return render_template('admin/system_settings.html',
        password_min_length=SystemSettings.get('password_min_length', '6'),
        notify_high_risk=SystemSettings.get('notify_high_risk', '0'),
        maintenance_mode=SystemSettings.get('maintenance_mode', '0'),
        system_version=SystemSettings.get('system_version', '1.0')
    )


@admin_bp.route('/backup')
@login_required
@admin_required
def backup():
    db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_path.startswith('sqlite:///'):
        path = db_path.replace('sqlite:///', '')
        if os.path.isabs(path):
            full_path = path
        else:
            full_path = os.path.join(current_app.root_path, path)
        if os.path.exists(full_path):
            log_action(current_user.id, 'backup', 'database_download')
            return send_file(full_path, as_attachment=True, download_name=f'phishdetector_backup_{datetime.now().strftime("%Y%m%d_%H%M")}.db')
    flash('النسخ الاحتياطي متاح لـ SQLite فقط', 'warning')
    return redirect(url_for('admin.system_settings'))


@admin_bp.route('/restore', methods=['GET', 'POST'])
@login_required
@admin_required
def restore():
    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        if f.filename and f.filename.endswith('.db'):
            db_path = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_path.startswith('sqlite:///'):
                path = db_path.replace('sqlite:///', '')
                full_path = os.path.join(current_app.root_path, path) if not os.path.isabs(path) else path
                f.save(full_path)
                log_action(current_user.id, 'restore', 'database_restore')
                flash('تم استعادة النسخة. أعد تشغيل التطبيق إن لزم.', 'success')
            else:
                flash('الاستعادة متاحة لـ SQLite فقط', 'error')
        else:
            flash('يرجى رفع ملف .db', 'error')
        return redirect(url_for('admin.system_settings'))
    return render_template('admin/restore.html')


@admin_bp.route('/templates')
@login_required
@admin_required
def templates_list():
    items = EmailTemplate.query.order_by(EmailTemplate.name).all()
    return render_template('admin/templates_list.html', items=items)


@admin_bp.route('/templates/<int:tid>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def template_edit(tid):
    t = EmailTemplate.query.get_or_404(tid)
    if request.method == 'POST':
        t.name = request.form.get('name', t.name)
        t.subject = request.form.get('subject', t.subject)
        t.body_html = request.form.get('body_html', t.body_html)
        t.body_text = request.form.get('body_text', t.body_text)
        t.is_active = request.form.get('is_active') == '1'
        db.session.commit()
        flash('تم تحديث القالب', 'success')
        return redirect(url_for('admin.templates_list'))
    return render_template('admin/template_edit.html', t=t)


@admin_bp.route('/templates/add', methods=['GET', 'POST'])
@login_required
@admin_required
def template_add():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip() or name.lower().replace(' ', '_')
        if name and not EmailTemplate.query.filter_by(slug=slug).first():
            t = EmailTemplate(name=name, slug=slug, subject=request.form.get('subject', ''), body_html=request.form.get('body_html', ''), body_text=request.form.get('body_text', ''))
            db.session.add(t)
            db.session.commit()
            flash('تم إضافة القالب', 'success')
            return redirect(url_for('admin.templates_list'))
        flash('الاسم مطلوب أو الرمز مستخدم', 'error')
    return render_template('admin/template_edit.html', t=None)


# ----- 5) سجل التحليلات والهجمات والمراقبة -----
@admin_bp.route('/analysis-log')
@login_required
@admin_required
def analysis_log():
    page = request.args.get('page', 1, type=int)
    per_page = 30
    q = AnalyzedEmail.query.order_by(AnalyzedEmail.created_at.desc())
    pagination = q.paginate(page=page, per_page=per_page)
    return render_template('admin/analysis_log.html', pagination=pagination)


@admin_bp.route('/attack-log')
@login_required
@admin_required
def attack_log():
    threats = Threat.query.order_by(Threat.created_at.desc()).limit(100).all()
    return render_template('admin/attack_log.html', threats=threats)


# ----- 6) رسائل داخلية ومهام -----
@admin_bp.route('/messages')
@login_required
@admin_required
def messages_inbox():
    received = InternalMessage.query.filter_by(receiver_id=current_user.id).order_by(InternalMessage.created_at.desc()).limit(50).all()
    sent = InternalMessage.query.filter_by(sender_id=current_user.id).order_by(InternalMessage.created_at.desc()).limit(30).all()
    return render_template('admin/messages_inbox.html', received=received, sent=sent)


@admin_bp.route('/messages/send', methods=['GET', 'POST'])
@login_required
@admin_required
def message_send():
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id', type=int)
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if subject and receiver_id:
            r = User.query.get(receiver_id)
            if r:
                m = InternalMessage(sender_id=current_user.id, receiver_id=receiver_id, subject=subject, body=body)
                db.session.add(m)
                db.session.commit()
                flash('تم إرسال الرسالة', 'success')
                return redirect(url_for('admin.messages_inbox'))
        flash('البيانات غير مكتملة', 'error')
    users = User.query.filter(User.id != current_user.id).order_by(User.full_name).all()
    return render_template('admin/message_send.html', users=users)


@admin_bp.route('/tasks')
@login_required
@admin_required
def tasks_list():
    tasks = Task.query.order_by(Task.created_at.desc()).limit(100).all()
    return render_template('admin/tasks_list.html', tasks=tasks)


@admin_bp.route('/tasks/add', methods=['GET', 'POST'])
@login_required
@admin_required
def task_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if title:
            t = Task(
                title=title,
                description=request.form.get('description', ''),
                priority=request.form.get('priority', 'medium'),
                assigned_to_id=request.form.get('assigned_to_id', type=int) or None,
                created_by_id=current_user.id
            )
            db.session.add(t)
            db.session.commit()
            flash('تم إضافة المهمة', 'success')
            return redirect(url_for('admin.tasks_list'))
        flash('العنوان مطلوب', 'error')
    users = User.query.order_by(User.full_name).all()
    return render_template('admin/task_edit.html', task=None, users=users)


@admin_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.title = request.form.get('title', task.title)
        task.description = request.form.get('description', task.description)
        task.status = request.form.get('status', task.status)
        task.priority = request.form.get('priority', task.priority)
        task.assigned_to_id = request.form.get('assigned_to_id', type=int) or None
        db.session.commit()
        flash('تم تحديث المهمة', 'success')
        return redirect(url_for('admin.tasks_list'))
    users = User.query.order_by(User.full_name).all()
    return render_template('admin/task_edit.html', task=task, users=users)


# ----- الإشعارات -----
@admin_bp.route('/notifications')
@login_required
@admin_required
def notifications_list():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    for n in items:
        n.is_read = True
    db.session.commit()
    return render_template('admin/notifications_list.html', items=items)
