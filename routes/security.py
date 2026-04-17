# Security Officer Routes - متاح للأدمن ومسؤول الأمن
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.email import AnalyzedEmail
from models.threat import Threat
from models.block_list import BlockList

security_bp = Blueprint('security', __name__, url_prefix='/security')


def security_or_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('admin', 'security'):
            return redirect(url_for('auth.landing'))
        return f(*args, **kwargs)
    return decorated


@security_bp.route('/')
@login_required
@security_or_admin_required
def index():
    return redirect(url_for('security.security_center'))


@security_bp.route('/center')
@login_required
@security_or_admin_required
def security_center():
    threats_count = Threat.query.filter(Threat.status == 'active').count()
    high_risk_count = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'high', AnalyzedEmail.status == 'pending').count()
    phishing_count = AnalyzedEmail.query.filter(AnalyzedEmail.risk_level == 'high').count()
    block_count = BlockList.query.count()
    recent_threats = Threat.query.order_by(Threat.created_at.desc()).limit(10).all()
    return render_template('security/security_center.html',
        threats_count=threats_count,
        high_risk_count=high_risk_count,
        phishing_count=phishing_count,
        block_count=block_count,
        recent_threats=recent_threats
    )


@security_bp.route('/block-lists', methods=['GET', 'POST'])
@login_required
@security_or_admin_required
def block_lists():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            value = request.form.get('value', '').strip()
            list_type = request.form.get('list_type', 'email')
            reason = request.form.get('reason', '').strip()
            if value and list_type in ('email', 'domain', 'url'):
                existing = BlockList.query.filter_by(value=value, list_type=list_type).first()
                if existing:
                    flash('هذا العنصر موجود مسبقاً في القائمة', 'warning')
                else:
                    entry = BlockList(value=value, list_type=list_type, reason=reason, added_by_id=current_user.id)
                    db.session.add(entry)
                    db.session.commit()
                    flash('تمت الإضافة إلى قائمة الحظر', 'success')
            else:
                flash('بيانات غير صالحة', 'error')
        elif action == 'delete':
            bid = request.form.get('block_id', type=int)
            if bid:
                entry = BlockList.query.get(bid)
                if entry:
                    db.session.delete(entry)
                    db.session.commit()
                    flash('تم الحذف من قائمة الحظر', 'success')
            return redirect(url_for('security.block_lists'))
    entries = BlockList.query.order_by(BlockList.created_at.desc()).all()
    return render_template('security/block_lists.html', entries=entries)


@security_bp.route('/threat-map')
@login_required
@security_or_admin_required
def threat_map():
    threats = Threat.query.order_by(Threat.created_at.desc()).all()
    by_country = {}
    for t in threats:
        cc = t.country_code or 'XX'
        by_country[cc] = by_country.get(cc, 0) + 1
    return render_template('security/threat_map.html', threats=threats, by_country=by_country)


@security_bp.route('/attack-details')
@login_required
@security_or_admin_required
def attack_details():
    threats = Threat.query.order_by(Threat.created_at.desc()).limit(50).all()
    return render_template('security/attack_details.html', threats=threats)


@security_bp.route('/suspicious-inbox', methods=['GET', 'POST'])
@login_required
@security_or_admin_required
def suspicious_inbox():
    if request.method == 'POST':
        action = request.form.get('action')
        email_id = request.form.get('email_id', type=int)
        if email_id:
            em = AnalyzedEmail.query.get(email_id)
            if em:
                if action == 'reviewed':
                    em.status = 'reviewed'
                    db.session.commit()
                    flash('تم تحديد الرسالة كمراجعة', 'success')
                elif action == 'blocked':
                    em.status = 'blocked'
                    db.session.commit()
                    flash('تم تحديد الرسالة كمحظورة', 'success')
        return redirect(url_for('security.suspicious_inbox'))
    items = AnalyzedEmail.query.filter(
        (AnalyzedEmail.risk_level == 'high') | (AnalyzedEmail.risk_level == 'medium')
    ).order_by(AnalyzedEmail.created_at.desc()).limit(50).all()
    return render_template('security/suspicious_inbox.html', items=items)


@security_bp.route('/report-threat', methods=['GET', 'POST'])
@login_required
@security_or_admin_required
def report_threat():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('العنوان مطلوب', 'error')
            return redirect(url_for('security.report_threat'))
        t = Threat(
            title=title,
            description=request.form.get('description', ''),
            severity=request.form.get('severity', 'medium'),
            source_ip=request.form.get('source_ip', ''),
            country_code=request.form.get('country_code', ''),
            status='active',
            created_by_id=current_user.id
        )
        db.session.add(t)
        db.session.commit()
        flash('تم تسجيل التهديد بنجاح', 'success')
        return redirect(url_for('security.attack_details'))
    return render_template('security/report_threat.html')
