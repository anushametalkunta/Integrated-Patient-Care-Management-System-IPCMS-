from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegistrationForm, LoginForm
from routes.api import log_audit
from datetime import datetime, timedelta

# Simple in-memory tracker: { email: [attempt_timestamps] }
failed_login_attempts = {}
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def is_locked_out(email):
    attempts = failed_login_attempts.get(email, [])
    cutoff = datetime.utcnow() - timedelta(minutes=LOCKOUT_MINUTES)
    recent = [t for t in attempts if t > cutoff]
    failed_login_attempts[email] = recent
    return len(recent) >= MAX_ATTEMPTS


def record_failed_attempt(email):
    failed_login_attempts.setdefault(email, []).append(datetime.utcnow())


def clear_failed_attempts(email):
    failed_login_attempts.pop(email, None)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if existing_user:
            flash('An account with that email already exists. Please log in.', 'danger')
            return redirect(url_for('auth.login'))

        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone_number=form.phone_number.data.strip(),
            role=form.role.data
        )
        user.set_password(form.password.data)  # securely hashed, never stored in plain text
        db.session.add(user)
        db.session.commit()

        flash(f'Account created successfully for {user.full_name} as {user.role}. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()

        if is_locked_out(email):
            flash(f'Too many failed login attempts. Please try again in {LOCKOUT_MINUTES} minutes.', 'danger')
            return render_template('login.html', form=form)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            clear_failed_attempts(email)
            login_user(user)
            log_audit(user.id, 'login_success', f'User logged in: {email}')
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            record_failed_attempt(email)
            log_audit(user.id if user else None, 'login_failed', f'Failed login attempt for: {email}')
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))