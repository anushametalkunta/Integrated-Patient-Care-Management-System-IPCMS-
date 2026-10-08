from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from models import Patient, Consultation, Prescription, LabTest, DiagnosisHistory, ElectronicHealthRecord
from decorators import roles_required

medical_history_bp = Blueprint('medical_history', __name__, url_prefix='/medical-history')


@medical_history_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def index():
    search = request.args.get('q', '').strip()
    patients = Patient.query
    if search:
        like = f'%{search}%'
        patients = patients.filter(or_(Patient.full_name.ilike(like), Patient.mrn.ilike(like)))
    patients = patients.order_by(Patient.full_name).all()

    timeline = []
    for p in patients[:20]:
        for d in p.diagnosis_history:
            timeline.append({'date': d.diagnosis_date, 'patient': p.full_name, 'type': 'Diagnosis', 'detail': d.diagnosis})
        if p.ehr and p.ehr.medical_history:
            timeline.append({'date': p.ehr.updated_at.date(), 'patient': p.full_name, 'type': 'History', 'detail': p.ehr.medical_history[:80]})
    timeline.sort(key=lambda x: x['date'], reverse=True)

    return render_template(
        'medical_history.html',
        patients=patients,
        timeline=timeline[:30],
        search=search,
        active_page='medical_history'
    )
