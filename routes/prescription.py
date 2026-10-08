from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import Prescription, Patient, Doctor
from forms import PrescriptionForm
from decorators import roles_required

prescription_bp = Blueprint('prescription', __name__, url_prefix='/prescriptions')


def _populate_form_choices(form):
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name)]
    form.doctor_id.choices = [(d.id, d.full_name) for d in Doctor.query.order_by(Doctor.full_name)]


@prescription_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def list_prescriptions():
    search = request.args.get('q', '').strip()
    query = Prescription.query.join(Patient).join(Doctor)
    if search:
        like = f'%{search}%'
        query = query.filter(or_(Patient.full_name.ilike(like), Prescription.medication_name.ilike(like)))
    prescriptions = query.order_by(Prescription.prescribed_date.desc()).all()
    return render_template(
        'prescriptions.html',
        prescriptions=prescriptions,
        total=len(prescriptions),
        search=search,
        active_page='prescriptions'
    )


@prescription_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def add_prescription():
    form = PrescriptionForm()
    _populate_form_choices(form)
    if form.validate_on_submit():
        db.session.add(Prescription(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            medication_name=form.medication_name.data.strip(),
            dosage=(form.dosage.data or '').strip() or None,
            frequency=(form.frequency.data or '').strip() or None,
            prescribed_date=form.prescribed_date.data,
            notes=(form.notes.data or '').strip() or None
        ))
        db.session.commit()
        flash('Prescription added.', 'success')
        return redirect(url_for('prescription.list_prescriptions'))
    return render_template('prescription_form.html', form=form, title='Add Prescription', active_page='prescriptions')
