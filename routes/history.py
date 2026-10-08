from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import Patient, Consultation, Prescription, LabTest, Allergy, DiagnosisHistory
from decorators import roles_required

history_bp = Blueprint('history', __name__, url_prefix='/medical-history')


@history_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def select_patient():
    patients = Patient.query.order_by(Patient.full_name).all()
    selected_id = request.args.get('patient_id', type=int)
    patient = Patient.query.get(selected_id) if selected_id else (patients[0] if patients else None)
    return _render_history(patient, patients)


@history_bp.route('/my')
@login_required
def my_history():
    if current_user.role != 'Patient':
        return redirect(url_for('history.select_patient'))

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Complete your patient profile first.', 'info')
        return redirect(url_for('patient.add_patient'))

    return _render_history(patient, [patient], is_patient_view=True)


def _render_history(patient, patients, is_patient_view=False):
    if not patient:
        return render_template('medical_history.html', patient=None, patients=patients)

    consultations = Consultation.query.filter_by(patient_id=patient.id).order_by(
        Consultation.consultation_date.desc()
    ).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient.id).order_by(
        Prescription.prescribed_date.desc()
    ).all()
    lab_tests = LabTest.query.filter_by(patient_id=patient.id).order_by(
        LabTest.test_date.desc()
    ).all()
    allergies = Allergy.query.filter_by(patient_id=patient.id).order_by(Allergy.created_at.desc()).all()
    diagnoses = DiagnosisHistory.query.filter_by(patient_id=patient.id).order_by(
        DiagnosisHistory.diagnosis_date.desc()
    ).all()

    summary = {
        'consultations': len(consultations),
        'prescriptions': len(prescriptions),
        'lab_tests': len(lab_tests),
        'allergies': len(allergies),
        'diagnoses': len(diagnoses),
    }

    return render_template(
        'medical_history.html',
        patient=patient,
        patients=patients,
        consultations=consultations,
        prescriptions=prescriptions,
        lab_tests=lab_tests,
        allergies=allergies,
        diagnoses=diagnoses,
        summary=summary,
        is_patient_view=is_patient_view,
    )
