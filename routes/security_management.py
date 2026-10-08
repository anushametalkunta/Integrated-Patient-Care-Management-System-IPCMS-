from datetime import datetime, timedelta
from collections import Counter

from flask import Blueprint, render_template
from flask_login import login_required

from models import User, AuditLog
from decorators import roles_required

security_management_bp = Blueprint(
    'security_management', __name__, url_prefix='/security-management'
)

# Static permission descriptions per role, shown next to the live user count
# for that role. Add a role here if you add one to the User model.
ROLE_PERMISSIONS = {
    'Admin': 'All Modules',
    'Doctor': 'Patient Records, Appointments, Prescriptions',
    'Nurse': 'Patients, Vital Signs, Appointments',
    'Pharmacist': 'Pharmacy, Medicine Inventory, Prescriptions',
    'Laboratory Staff': 'Lab Reports, Test Results',
    'Patient': 'Own Records, Appointments',
}


@security_management_bp.route('/')
@login_required
@roles_required('Admin')
def index():
    role_counts = Counter(u.role for u in User.query.all())
    roles_table = [
        {'role': role, 'users': role_counts.get(role, 0), 'permissions': perms}
        for role, perms in ROLE_PERMISSIONS.items()
    ]

    since = datetime.utcnow() - timedelta(days=7)
    recent_logs = AuditLog.query.filter(AuditLog.created_at >= since).all()

    failed_logins = len([a for a in recent_logs if a.action == 'login_failed'])
    unauthorized_attempts = len([a for a in recent_logs if a.action == 'unauthorized_access'])

    # 7-day trend of unauthorized access attempts, for the chart
    chart_labels, chart_data = [], []
    for i in range(6, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).date()
        day_count = len([
            a for a in recent_logs
            if a.action == 'unauthorized_access' and a.created_at.date() == day
        ])
        chart_labels.append(day.strftime('%d %b'))
        chart_data.append(day_count)

    recent_unauthorized = sorted(
        [a for a in recent_logs if a.action == 'unauthorized_access'],
        key=lambda a: a.created_at,
        reverse=True
    )[:10]

    # Simple threshold-based status badge; tune the numbers as needed
    security_secure = failed_logins < 20 and unauthorized_attempts < 10

    return render_template(
        'security_management.html',
        active_page='security_management',
        roles_table=roles_table,
        failed_logins=failed_logins,
        unauthorized_attempts=unauthorized_attempts,
        chart_labels=chart_labels,
        chart_data=chart_data,
        recent_unauthorized=recent_unauthorized,
        security_secure=security_secure,
    )