# Manager Routes - متاح للأدمن ومدير القسم
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models.user import User
from models.email import AnalyzedEmail

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


def manager_or_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role not in ('admin', 'manager'):
            return redirect(url_for('auth.landing'))
        return f(*args, **kwargs)
    return decorated


def get_team_users():
    """المستخدمون في نفس القسم (أو الكل للأدمن)"""
    if current_user.role == 'admin':
        return User.query.filter(User.role != 'admin').order_by(User.department, User.full_name).all()
    return User.query.filter_by(department=current_user.department).order_by(User.full_name).all()


@manager_bp.route('/')
@login_required
@manager_or_admin_required
def index():
    return redirect(url_for('manager.department_dashboard'))


@manager_bp.route('/dashboard')
@login_required
@manager_or_admin_required
def department_dashboard():
    team = get_team_users()
    team_ids = [u.id for u in team]
    total_analyzed = AnalyzedEmail.query.filter(AnalyzedEmail.analyzed_by_id.in_(team_ids)).count() if team_ids else 0
    high_risk = AnalyzedEmail.query.filter(
        AnalyzedEmail.analyzed_by_id.in_(team_ids),
        AnalyzedEmail.risk_level == 'high'
    ).count() if team_ids else 0
    recent_activity = []
    if team_ids:
        recent_activity = AnalyzedEmail.query.filter(
            AnalyzedEmail.analyzed_by_id.in_(team_ids)
        ).order_by(AnalyzedEmail.created_at.desc()).limit(10).all()
    return render_template('manager/department_dashboard.html',
        team_count=len(team),
        total_analyzed=total_analyzed,
        high_risk=high_risk,
        recent_activity=recent_activity
    )


@manager_bp.route('/my-team')
@login_required
@manager_or_admin_required
def my_team():
    team = get_team_users()
    team_stats = []
    for u in team:
        total = AnalyzedEmail.query.filter_by(analyzed_by_id=u.id).count()
        high = AnalyzedEmail.query.filter_by(analyzed_by_id=u.id, risk_level='high').count()
        team_stats.append({'user': u, 'total': total, 'high_risk': high})
    return render_template('manager/my_team.html', team_stats=team_stats)


@manager_bp.route('/department-reports')
@login_required
@manager_or_admin_required
def department_reports():
    team = get_team_users()
    reports = []
    total_all = 0
    high_all = 0
    for u in team:
        cnt = AnalyzedEmail.query.filter_by(analyzed_by_id=u.id).count()
        high = AnalyzedEmail.query.filter_by(analyzed_by_id=u.id, risk_level='high').count()
        total_all += cnt
        high_all += high
        reports.append({'user': u, 'total': cnt, 'high_risk': high})
    return render_template('manager/department_reports.html', reports=reports, total_all=total_all, high_all=high_all)
