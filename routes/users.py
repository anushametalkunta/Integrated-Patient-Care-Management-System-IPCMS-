from flask import Blueprint, render_template
from flask_login import login_required

from models import User
from decorators import roles_required

users_bp = Blueprint('users', __name__, url_prefix='/users')


@users_bp.route('/')
@login_required
@roles_required('Admin')
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users, active_page='users')
