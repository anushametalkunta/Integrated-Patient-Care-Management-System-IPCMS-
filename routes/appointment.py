from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import Appointment, Patient, Doctor
from forms import AppointmentForm
from decorators import roles_required
from routes.api import create_notification

appointment_bp = Blueprint('appointment', __name__, url_prefix='/appointments')


@appointment_bp.route('/')
@login_required
def list_appointments():
    if current_user.role == 'Admin' or current_user.role == 'Nurse':
        appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    elif current_user.role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        appointments = Appointment.query.filter_by(doctor_id=doctor.id).all() if doctor else []
    else:  # Patient
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        appointments = Appointment.query.filter_by(patient_id=patient.id).all() if patient else []

    return render_template('appointments.html', appointments=appointments, active_page='appointments')


@appointment_bp.route('/book', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse', 'Patient')
def book_appointment():
    form = AppointmentForm()
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name).all()]
    form.doctor_id.choices = [(d.id, f'Dr. {d.full_name} ({d.specialization})')
                               for d in Doctor.query.order_by(Doctor.full_name).all()]

    if current_user.role == 'Patient':
        my_patient = Patient.query.filter_by(user_id=current_user.id).first()
        if not my_patient:
            flash('Please complete your patient profile before booking an appointment.', 'warning')
            return redirect(url_for('patient.add_patient'))
        form.patient_id.choices = [(my_patient.id, my_patient.full_name)]

    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data
        )
        db.session.add(appointment)
        db.session.commit()

        db.session.add(appointment)
        db.session.commit()

        patient_obj = Patient.query.get(appointment.patient_id)
        if patient_obj and patient_obj.user_id:
            create_notification(
                patient_obj.user_id, 'appointment', 'Appointment Booked',
                f'Your appointment on {appointment.appointment_date} at {appointment.appointment_time} has been scheduled.'
            )

        doctor_obj = Doctor.query.get(appointment.doctor_id)
        if doctor_obj and doctor_obj.user_id:
            patient_name = patient_obj.full_name if patient_obj else 'A patient'
            create_notification(
                doctor_obj.user_id, 'appointment', 'New Appointment',
                f'{patient_name} has booked an appointment with you on {appointment.appointment_date} at {appointment.appointment_time}.'
            )

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('appointment.list_appointments'))

    return render_template('appointment_form.html', form=form)


@appointment_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)

    allowed = current_user.role in ('Admin', 'Nurse')
    if current_user.role == 'Patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        allowed = bool(patient and appointment.patient_id == patient.id)

    if not allowed:
        flash('You are not authorized to cancel this appointment.', 'danger')
        return redirect(url_for('appointment.list_appointments'))

    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointment.list_appointments'))
