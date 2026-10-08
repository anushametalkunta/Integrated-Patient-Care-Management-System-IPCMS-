from flask import Blueprint, render_template
from flask_login import login_required, current_user

from config import Config

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/')
@login_required
def index():
    return render_template(
        'settings.html',
        user=current_user,
        db_uri=Config.SQLALCHEMY_DATABASE_URI.split('/')[-1] if Config.SQLALCHEMY_DATABASE_URI else 'sqlite',
        active_page='settings'
    )
