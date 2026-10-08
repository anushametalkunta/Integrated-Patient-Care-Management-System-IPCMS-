import csv
import io
from datetime import datetime
from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from extensions import db
from models import Feedback, Patient, Doctor, Consultation
from decorators import roles_required

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')


# ---------- Patient: submit feedback after a consultation ----------

@feedback_bp.route('/submit/<int:consultation_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Patient')
def submit_feedback(consultation_id):
    consultation = Consultation.query.get_or_404(consultation_id)
    patient = Patient.query.filter_by(user_id=current_user.id).first()

    if not patient or consultation.patient_id != patient.id:
        flash('You can only leave feedback for your own consultations.', 'error')
        return redirect(url_for('dashboard.index'))

    if consultation.feedback:
        flash('You have already submitted feedback for this consultation.', 'info')
        return redirect(url_for('feedback.my_feedback'))

    if request.method == 'POST':
        try:
            doctor_rating = int(request.form.get('doctor_rating', 0))
            hospital_rating = int(request.form.get('hospital_rating', 0))
            lab_rating = int(request.form.get('lab_rating', 0))
            pharmacy_rating = int(request.form.get('pharmacy_rating', 0))
        except ValueError:
            flash('Ratings must be numbers between 1 and 5.', 'error')
            return redirect(request.url)

        ratings = [doctor_rating, hospital_rating, lab_rating, pharmacy_rating]
        if any(r < 1 or r > 5 for r in ratings):
            flash('All ratings must be between 1 and 5 stars.', 'error')
            return redirect(request.url)

        fb = Feedback(
            patient_id=patient.id,
            doctor_id=consultation.doctor_id,
            consultation_id=consultation.id,
            doctor_rating=doctor_rating,
            hospital_rating=hospital_rating,
            lab_rating=lab_rating,
            pharmacy_rating=pharmacy_rating,
            comments=request.form.get('comments', '').strip() or None
        )
        db.session.add(fb)
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback.my_feedback'))

    return render_template('feedback_form.html', consultation=consultation, active_page='feedback')


@feedback_bp.route('/mine')
@login_required
@roles_required('Patient')
def my_feedback():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    entries = []
    if patient:
        entries = Feedback.query.filter_by(patient_id=patient.id).order_by(Feedback.created_at.desc()).all()
    return render_template('feedback_list.html', feedback_entries=entries, is_admin_view=False,
                            doctors=None, active_page='feedback')


# ---------- Admin/Doctor/Nurse: view all feedback with filters ----------

def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _filtered_feedback():
    query = Feedback.query
    doctor_id = request.args.get('doctor_id', type=int)
    department = request.args.get('department', '').strip()
    rating = request.args.get('rating', type=int)
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))

    if doctor_id:
        query = query.filter(Feedback.doctor_id == doctor_id)
    if start:
        query = query.filter(db.func.date(Feedback.created_at) >= start)
    if end:
        query = query.filter(db.func.date(Feedback.created_at) <= end)

    entries = query.order_by(Feedback.created_at.desc()).all()

    if department:
        entries = [e for e in entries if e.doctor and e.doctor.department == department]
    if rating:
        entries = [e for e in entries if round(e.overall_rating) == rating]

    return entries


@feedback_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def index():
    entries = _filtered_feedback()

    avg_doctor = round(sum(e.doctor_rating for e in entries) / len(entries), 2) if entries else 0
    avg_hospital = round(sum(e.hospital_rating for e in entries) / len(entries), 2) if entries else 0
    avg_lab = round(sum(e.lab_rating for e in entries) / len(entries), 2) if entries else 0
    avg_pharmacy = round(sum(e.pharmacy_rating for e in entries) / len(entries), 2) if entries else 0
    avg_overall = round(sum(e.overall_rating for e in entries) / len(entries), 2) if entries else 0

    departments = sorted({d.department for d in Doctor.query.all()})

    return render_template(
        'feedback_list.html',
        feedback_entries=entries,
        is_admin_view=True,
        doctors=Doctor.query.order_by(Doctor.full_name).all(),
        departments=departments,
        avg_doctor=avg_doctor,
        avg_hospital=avg_hospital,
        avg_lab=avg_lab,
        avg_pharmacy=avg_pharmacy,
        avg_overall=avg_overall,
        total_feedback=len(entries),
        active_page='feedback'
    )


@feedback_bp.route('/<int:feedback_id>')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def view_feedback(feedback_id):
    fb = Feedback.query.get_or_404(feedback_id)
    return render_template('feedback_detail.html', fb=fb, active_page='feedback')


@feedback_bp.route('/export/csv')
@login_required
@roles_required('Admin')
def export_csv():
    entries = _filtered_feedback()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Patient', 'Doctor', 'Department', 'Doctor Rating',
                      'Hospital Rating', 'Lab Rating', 'Pharmacy Rating', 'Overall', 'Comments'])
    for e in entries:
        writer.writerow([
            e.created_at.strftime('%Y-%m-%d %H:%M'),
            e.patient.full_name, e.doctor.full_name, e.doctor.department,
            e.doctor_rating, e.hospital_rating, e.lab_rating, e.pharmacy_rating,
            e.overall_rating, e.comments or ''
        ])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=feedback_report.csv'}
    )