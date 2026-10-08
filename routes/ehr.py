from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import Patient, ElectronicHealthRecord, Allergy, DiagnosisHistory
from forms import EHRForm, AllergyForm, DiagnosisForm
from decorators import roles_required

ehr_bp = Blueprint('ehr', __name__, url_prefix='/ehr')


def _can_view_patient_ehr(patient):
    if current_user.role == 'Patient':
        return patient.user_id == current_user.id
    return current_user.role in ('Admin', 'Doctor', 'Nurse')


def _filter_patients(query):
    search = request.args.get('q', '').strip()
    if search:
        like = f'%{search}%'
        query = query.filter(
            or_(
                Patient.full_name.ilike(like),
                Patient.mrn.ilike(like),
                Patient.contact_number.ilike(like)
            )
        )
    return query.order_by(Patient.full_name)


@ehr_bp.route('/')
@login_required
def list_records():
    if current_user.role == 'Patient':
        return redirect(url_for('ehr.my_record'))

    patients = _filter_patients(Patient.query).all()
    selected_id = request.args.get('patient', type=int)
    selected = Patient.query.get(selected_id) if selected_id else (patients[0] if patients else None)
    record = None
    if selected:
        record = ElectronicHealthRecord.query.filter_by(patient_id=selected.id).first()

    return render_template(
        'ehr_list.html',
        patients=patients,
        selected=selected,
        record=record,
        total=len(patients),
        active_page='ehr',
        can_edit=current_user.role in ('Admin', 'Doctor', 'Nurse')
    )


@ehr_bp.route('/my-record')
@login_required
def my_record():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Complete your patient profile first.', 'info')
        return redirect(url_for('patient.add_patient'))
    return redirect(url_for('ehr.view_record', patient_id=patient.id))


@ehr_bp.route('/view/<int:patient_id>')
@login_required
def view_record(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not _can_view_patient_ehr(patient):
        abort(403)

    record = ElectronicHealthRecord.query.filter_by(patient_id=patient.id).first()
    allergies = Allergy.query.filter_by(patient_id=patient.id).all()
    diagnoses = DiagnosisHistory.query.filter_by(patient_id=patient.id).order_by(
        DiagnosisHistory.diagnosis_date.desc()
    ).all()
    can_edit = current_user.role in ('Admin', 'Doctor', 'Nurse')

    return render_template(
        'ehr_view.html',
        patient=patient,
        record=record,
        ehr=record,
        allergies=allergies,
        diagnoses=diagnoses,
        can_edit=can_edit,
        allergy_form=AllergyForm(),
        diagnosis_form=DiagnosisForm(),
        active_page='ehr'
    )


@ehr_bp.route('/patient/<int:patient_id>')
@login_required
def view_record_legacy(patient_id):
    return redirect(url_for('ehr.view_record', patient_id=patient_id))


@ehr_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def edit_record(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    record = ElectronicHealthRecord.query.filter_by(patient_id=patient.id).first()
    is_new = record is None

    form = EHRForm(obj=record)
    if form.validate_on_submit():
        if record is None:
            record = ElectronicHealthRecord(patient_id=patient.id)
            db.session.add(record)

        record.medical_summary = (form.medical_summary.data or '').strip() or None
        record.medical_history = (form.medical_history.data or '').strip() or None
        record.chronic_diseases = (form.chronic_diseases.data or '').strip() or None
        record.allergies = (form.allergies.data or '').strip() or None
        record.diagnoses = (form.diagnoses.data or '').strip() or None
        record.medications = (form.medications.data or '').strip() or None
        record.treatment_notes = (form.treatment_notes.data or '').strip() or None
        record.update_vitals(form.height_cm.data, form.weight_kg.data)
        record.updated_at = datetime.utcnow()
        db.session.commit()

        flash(f'EHR {"created" if is_new else "updated"} for {patient.full_name}.', 'success')
        return redirect(url_for('ehr.view_record', patient_id=patient.id))

    return render_template(
        'ehr_form.html',
        form=form,
        patient=patient,
        title='Create EHR' if is_new else 'Edit EHR Record',
        is_new=is_new,
        active_page='ehr'
    )


@ehr_bp.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def edit_record_legacy(patient_id):
    return edit_record(patient_id)


@ehr_bp.route('/allergy/add/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def add_allergy(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = AllergyForm()
    if form.validate_on_submit():
        db.session.add(Allergy(
            patient_id=patient.id,
            allergy_name=form.allergy_name.data.strip(),
            reaction=(form.reaction.data or '').strip() or None
        ))
        db.session.commit()
        flash('Allergy added.', 'success')
    return redirect(url_for('ehr.view_record', patient_id=patient.id))


@ehr_bp.route('/diagnosis/add/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def add_diagnosis(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = DiagnosisForm()
    if form.validate_on_submit():
        db.session.add(DiagnosisHistory(
            patient_id=patient.id,
            diagnosis_date=form.diagnosis_date.data,
            diagnosis=form.diagnosis.data.strip(),
            notes=(form.notes.data or '').strip() or None
        ))
        db.session.commit()
        flash('Diagnosis entry added.', 'success')
    return redirect(url_for('ehr.view_record', patient_id=patient.id))
