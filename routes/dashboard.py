import json
import time
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from models import (
    Patient, Doctor, Appointment, User, Consultation,
    Prescription, LabTest, Medicine, Bill, BillItem, AuditLog, Notification, Feedback
)
from utils import monthly_counts

dashboard_bp = Blueprint('dashboard', __name__)

# --- Simple in-memory cache for chart data (Day 5 performance optimization) ---
# Chart data is identical for every viewer at a given moment, so recomputing
# it on every single dashboard load is wasted work. Cache it for 60 seconds.
_chart_cache = {'data': None, 'expires_at': 0}
CACHE_TTL_SECONDS = 60


def _chart_data():
    now = time.time()
    if _chart_cache['data'] is not None and now < _chart_cache['expires_at']:
        return _chart_cache['data']

    consultations = Consultation.query.all()
    patients = Patient.query.all()
    prescriptions = Prescription.query.all()
    lab_tests = LabTest.query.all()

    consult_labels, consult_data = monthly_counts(consultations, 'consultation_date')
    patient_labels, patient_data = monthly_counts(patients, 'created_at')

    med_counts = Counter(p.medication_name for p in prescriptions)
    top_meds = med_counts.most_common(5)
    rx_labels = [m[0] for m in top_meds] or ['No data']
    rx_data = [m[1] for m in top_meds] or [0]

    cat_counts = Counter(t.category for t in lab_tests)
    lab_labels = list(cat_counts.keys()) or ['No data']
    lab_data = list(cat_counts.values()) or [0]

    gender_counts = Counter(p.gender for p in patients)
    gender_labels = list(gender_counts.keys()) or ['No data']
    gender_data = list(gender_counts.values()) or [0]

    # Doctor-wise consultations (single aggregated query, not a Python loop)
    doctor_counts = (
        db_session_query_doctor_counts()
    )
    doctor_labels = [d[0] for d in doctor_counts] or ['No data']
    doctor_data = [d[1] for d in doctor_counts] or [0]

    # Appointment trends (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_appts = Appointment.query.filter(Appointment.appointment_date >= thirty_days_ago).all()
    day_buckets = {}
    for a in recent_appts:
        day = a.appointment_date.strftime('%d %b')
        day_buckets.setdefault(day, {'Scheduled': 0, 'Completed': 0, 'Cancelled': 0})
        status = getattr(a, 'status', 'Scheduled')
        if status not in day_buckets[day]:
            day_buckets[day][status] = 0
        day_buckets[day][status] += 1
    trend_labels = list(day_buckets.keys())
    trend_scheduled = [x.get('Scheduled', 0) for x in day_buckets.values()]
    trend_completed = [x.get('Completed', 0) for x in day_buckets.values()]
    trend_cancelled = [x.get('Cancelled', 0) for x in day_buckets.values()]

    # --- NEW: Disease Distribution (top diagnoses from Consultation records) ---
    diagnosis_counts = Counter(
        (c.diagnosis or 'Unspecified').strip() for c in consultations if c.diagnosis
    )
    top_diagnoses = diagnosis_counts.most_common(6)
    disease_labels = [d[0] for d in top_diagnoses] or ['No data']
    disease_data = [d[1] for d in top_diagnoses] or [0]

    # --- NEW: Revenue Analysis (paid revenue per month, last 6 months) ---
    paid_items = (
        BillItem.query.join(Bill, Bill.id == BillItem.bill_id)
        .filter(Bill.payment_status == 'Paid').all()
    )
    revenue_by_month = Counter()
    for item in paid_items:
        key = item.bill.bill_date.strftime('%b %Y')
        revenue_by_month[key] += item.amount

    # Build the last 6 calendar months in order, oldest to newest
    today = date.today()
    cursor = today.replace(day=1)
    months_back = []
    for i in range(5, -1, -1):
        year = cursor.year
        month = cursor.month - i
        while month <= 0:
            month += 12
            year -= 1
        months_back.append(date(year, month, 1).strftime('%b %Y'))
    revenue_labels = months_back
    revenue_data = [round(revenue_by_month.get(m, 0), 2) for m in revenue_labels]

    data = {
        'consult_labels': consult_labels,
        'consult_data': consult_data,
        'patient_labels': patient_labels,
        'patient_data': patient_data,
        'rx_labels': rx_labels,
        'rx_data': rx_data,
        'lab_labels': lab_labels,
        'lab_data': lab_data,
        'gender_labels': gender_labels,
        'gender_data': gender_data,
        'doctor_labels': doctor_labels,
        'doctor_data': doctor_data,
        'trend_labels': trend_labels,
        'trend_scheduled': trend_scheduled,
        'trend_completed': trend_completed,
        'trend_cancelled': trend_cancelled,
        'disease_labels': disease_labels,
        'disease_data': disease_data,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
    }

    _chart_cache['data'] = data
    _chart_cache['expires_at'] = now + CACHE_TTL_SECONDS
    return data


def db_session_query_doctor_counts():
    from extensions import db
    return (
        db.session.query(Doctor.full_name, func.count(Consultation.id))
        .join(Consultation, Consultation.doctor_id == Doctor.id)
        .group_by(Doctor.full_name)
        .order_by(func.count(Consultation.id).desc())
        .limit(8)
        .all()
    )


@dashboard_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    from extensions import db

    charts = _chart_data()

    total_revenue = (
        db.session.query(func.coalesce(func.sum(BillItem.amount), 0))
        .join(Bill, Bill.id == BillItem.bill_id)
        .filter(Bill.payment_status == 'Paid')
        .scalar()
    )

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    all_feedback = Feedback.query.order_by(Feedback.created_at.desc()).all()
    avg_satisfaction = round(sum(f.overall_rating for f in all_feedback) / len(all_feedback), 2) if all_feedback else 0
    recent_feedback = all_feedback[:5]
    stats = {
        'total_patients': Patient.query.count(),
        'total_doctors': Doctor.query.count(),
        'total_consultations': Consultation.query.count(),
        'total_prescriptions': Prescription.query.count(),
        'total_lab_tests': LabTest.query.count(),
        'total_appointments': Appointment.query.count(),
        'today_appointments': Appointment.query.filter_by(appointment_date=date.today()).count(),
        'total_medicines': Medicine.query.count(),
        'low_stock_medicines': Medicine.query.filter(Medicine.stock <= 10).count(),
        'total_bills': Bill.query.count(),
        'pending_bills': Bill.query.filter_by(payment_status='Pending').count(),
        'cancelled_appointments': Appointment.query.filter_by(status='Cancelled').count(),
        'pending_lab_reports': LabTest.query.filter_by(status='Pending').count(),
        'total_revenue': total_revenue,
        'unread_notifications': unread_notifications,
        'total_feedback': len(all_feedback),
        'avg_satisfaction': avg_satisfaction,
    }

    if current_user.role == 'Admin':
        stats['total_nurses'] = User.query.filter_by(role='Nurse').count()
        recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(8).all()
        recent_logins = AuditLog.query.filter(
            AuditLog.action.in_(['login_success', 'login_failed'])
        ).order_by(AuditLog.created_at.desc()).limit(10).all()
        recent_activity = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(15).all()
        return render_template(
            'dashboard_admin.html',
            stats=stats,
            charts=charts,
            recent_patients=recent_patients,
            recent_logins=recent_logins,
            recent_activity=recent_activity,
            recent_feedback=recent_feedback,
            active_page='dashboard'
        )
    if current_user.role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        appointments = []
        if doctor:
            appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
                Appointment.appointment_date.desc()
            ).limit(10).all()
        return render_template(
            'dashboard_doctor.html',
            doctor=doctor,
            appointments=appointments,
            stats=stats,
            charts=charts,
            active_page='dashboard'
        )

    if current_user.role == 'Nurse':
        patients = Patient.query.order_by(Patient.created_at.desc()).limit(10).all()
        return render_template(
            'dashboard_nurse.html',
            stats=stats,
            patients=patients,
            charts=charts,
            active_page='dashboard'
        )

    if current_user.role == 'Patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        appointments = []
        if patient:
            appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
                Appointment.appointment_date.desc()
            ).all()
        return render_template(
            'dashboard_patient.html',
            patient=patient,
            appointments=appointments,
            stats=stats,
            active_page='dashboard'
        )

    return redirect(url_for('auth.login'))