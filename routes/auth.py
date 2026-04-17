from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User
from models.password_reset import PasswordResetToken

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/landing')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    return render_template('public/landing.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and not getattr(user, 'is_active', True):
            flash('هذا الحساب معطّل. تواصل مع المدير.', 'error')
        elif user and user.check_password(password):
            login_user(user, remember=bool(remember))
            from utils.audit import log_action
            log_action(user.id, 'login', f'username={user.username}')
            flash('تم تسجيل الدخول بنجاح! مرحباً بك', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.dashboard_redirect'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', 'عام')

        # Validation
        errors = []
        if not full_name or not username or not email or not password:
            errors.append('جميع الحقول مطلوبة')
        if password != confirm_password:
            errors.append('كلمتا المرور غير متطابقتين')
        if len(password) < 6:
            errors.append('كلمة المرور يجب أن تكون 6 أحرف على الأقل')
        if User.query.filter_by(username=username).first():
            errors.append('اسم المستخدم مستخدم بالفعل')
        if User.query.filter_by(email=email).first():
            errors.append('البريد الإلكتروني مسجل بالفعل')

        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            user = User(
                full_name=full_name,
                username=username,
                email=email,
                department=department,
                role='employee'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    from utils.audit import log_action
    uid = getattr(current_user, 'id', None)
    uname = getattr(current_user, 'username', '')
    logout_user()
    if uid:
        log_action(uid, 'logout', f'username={uname}')
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.landing'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('لا يوجد حساب مرتبط بهذا البريد الإلكتروني.', 'error')
            return render_template('auth/forgot_password.html')
        token = PasswordResetToken.create_for_user(user, expires_hours=2)
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        try:
            from utils.mail import send_password_reset_email
            send_password_reset_email(user.email, reset_url)
            flash('تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني.', 'success')
        except Exception:
            flash('رابط إعادة التعيين (صالح لمدة ساعتين):', 'info')
            flash(reset_url, 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
    user = PasswordResetToken.get_user_by_token(token)
    if not user:
        flash('الرابط منتهي الصلاحية أو غير صالح. اطلب رابطاً جديداً.', 'error')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not password or len(password) < 6:
            flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل.', 'error')
            return render_template('auth/reset_password.html', token=token)
        if password != confirm:
            flash('كلمتا المرور غير متطابقتين.', 'error')
            return render_template('auth/reset_password.html', token=token)
        user.set_password(password)
        db.session.commit()
        PasswordResetToken.invalidate(token)
        flash('تم تغيير كلمة المرور بنجاح. يمكنك تسجيل الدخول الآن.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect user to their role-specific dashboard - الأدمن يروح لوحة الأدمن"""
    role = current_user.role
    if role == 'admin':
        return redirect(url_for('admin.org_dashboard'))
    elif role == 'security':
        return redirect(url_for('security.security_center'))
    elif role == 'manager':
        return redirect(url_for('manager.department_dashboard'))
    else:
        return redirect(url_for('employee.dashboard'))
