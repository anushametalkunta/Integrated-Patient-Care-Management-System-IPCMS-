import json
import os

from flask import Blueprint, render_template
from flask_login import login_required
from decorators import roles_required

deployment_status_bp = Blueprint('deployment_status', __name__, url_prefix='/deployment-status')

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
SMOKE_RESULTS_FILE = os.path.join(BASE_DIR, 'smoke_test_results.json')


@deployment_status_bp.route('/')
@login_required
@roles_required('Admin')
def index():
    backups = []
    if os.path.exists(BACKUP_DIR):
        for fname in sorted(os.listdir(BACKUP_DIR), reverse=True):
            path = os.path.join(BACKUP_DIR, fname)
            backups.append({
                'name': fname,
                'size_kb': round(os.path.getsize(path) / 1024, 1),
                'modified': os.path.getmtime(path)
            })

    smoke_data = None
    if os.path.exists(SMOKE_RESULTS_FILE):
        with open(SMOKE_RESULTS_FILE) as f:
            smoke_data = json.load(f)

    return render_template(
        'deployment_status.html',
        backups=backups,
        smoke_data=smoke_data,
        active_page='deployment_status'
    )