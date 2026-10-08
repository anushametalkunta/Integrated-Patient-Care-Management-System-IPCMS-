from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from extensions import db
from models import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()
    ).all()
    return render_template('notifications.html', notifications=notifications, active_page='notifications')


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id == current_user.id:
        n.is_read = True
        db.session.commit()
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id == current_user.id:
        db.session.delete(n)
        db.session.commit()
    return redirect(url_for('notifications.index'))