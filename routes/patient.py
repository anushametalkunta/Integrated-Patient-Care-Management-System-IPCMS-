from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from sqlalchemy import or_
from models import Patient
from forms import PatientForm
from decorators import roles_required

patient_bp = Blueprint('patient', __name__, url_prefix='/patients')


@patient_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def list_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    for p in patients:
        if not p.mrn:
            p.ensure_mrn()
    db.session.commit()
    return render_template('patients.html', patients=patients, active_page='patients')


@patient_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse', 'Patient')
def add_patient():
    # A logged-in Patient completing their own profile only gets one record.
    if current_user.role == 'Patient' and Patient.query.filter_by(user_id=current_user.id).first():
        flash('Your patient profile already exists. You can edit it instead.', 'info')
        return redirect(url_for('dashboard.index'))

    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            full_name=form.full_name.data.strip(),
            age=form.age.data,
            gender=form.gender.data,
            contact_number=form.contact_number.data.strip(),
            address=form.address.data.strip(),
            blood_group=form.blood_group.data,
            aadhaar_number=form.aadhaar_number.data.strip() if form.aadhaar_number.data else None,
            user_id=current_user.id if current_user.role == 'Patient' else None
        )
        db.session.add(patient)
        db.session.commit()
        patient.ensure_mrn()
        db.session.commit()
        flash(f'Patient record created for {patient.full_name}.', 'success')
        if current_user.role == 'Patient':
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('patient.list_patients'))

    return render_template('patient_form.html', form=form, title='Register Patient')


@patient_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse', 'Patient')
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    if current_user.role == 'Patient' and patient.user_id != current_user.id:
        flash('You can only edit your own profile.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash('Patient profile updated successfully.', 'success')
        if current_user.role == 'Patient':
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('patient.list_patients'))

    return render_template('patient_form.html', form=form, title='Edit Patient Profile')


@patient_bp.route('/delete/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Nurse')
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient record deleted.', 'info')
    return redirect(url_for('patient.list_patients'))
@patient_bp.route('/search')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def search_patients():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        like = f'%{q}%'
        results = Patient.query.filter(or_(
            Patient.full_name.ilike(like),
            Patient.contact_number.ilike(like),
            Patient.mrn.ilike(like),
            Patient.aadhaar_number.ilike(like)
        )).all()
    return render_template('patients.html', patients=results, active_page='patients', search=q)