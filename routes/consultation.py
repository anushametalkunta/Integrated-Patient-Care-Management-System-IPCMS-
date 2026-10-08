from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_

from extensions import db
from models import Consultation, Patient, Doctor
from forms import ConsultationForm
from decorators import roles_required

consultation_bp = Blueprint('consultation', __name__, url_prefix='/consultations')


def _populate_form_choices(form):
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name)]
    form.doctor_id.choices = [(d.id, d.full_name) for d in Doctor.query.order_by(Doctor.full_name)]


@consultation_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def list_consultations():
    search = request.args.get('q', '').strip()
    query = Consultation.query.join(Patient).join(Doctor)
    if search:
        like = f'%{search}%'
        query = query.filter(or_(Patient.full_name.ilike(like), Consultation.diagnosis.ilike(like)))
    consultations = query.order_by(Consultation.consultation_date.desc()).all()
    return render_template(
        'consultations.html',
        consultations=consultations,
        total=len(consultations),
        search=search,
        active_page='consultations'
    )


@consultation_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def add_consultation():
    form = ConsultationForm()
    _populate_form_choices(form)
    if form.validate_on_submit():
        db.session.add(Consultation(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            consultation_date=form.consultation_date.data,
            diagnosis=(form.diagnosis.data or '').strip() or None,
            follow_up_date=form.follow_up_date.data,
            notes=(form.notes.data or '').strip() or None
        ))
        db.session.commit()
        flash('Consultation record added.', 'success')
        return redirect(url_for('consultation.list_consultations'))
    return render_template('consultation_form.html', form=form, title='Add Consultation', active_page='consultations')
