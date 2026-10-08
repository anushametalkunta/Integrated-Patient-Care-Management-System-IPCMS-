from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from models import Doctor
from forms import DoctorForm
from decorators import roles_required

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctors')


@doctor_bp.route('/')
@login_required
def list_doctors():
    # Everyone logged in can view the doctor directory (e.g. patients choosing a doctor)
    doctors = Doctor.query.order_by(Doctor.full_name).all()
    return render_template('doctors.html', doctors=doctors, active_page='doctors')


@doctor_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def add_doctor():
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor(
            full_name=form.full_name.data.strip(),
            specialization=form.specialization.data.strip(),
            qualification=form.qualification.data.strip(),
            department=form.department.data.strip(),
            contact_number=form.contact_number.data.strip(),
            email=form.email.data.lower().strip(),
            available_time=form.available_time.data.strip()
        )
        db.session.add(doctor)
        db.session.commit()
        flash(f'Dr. {doctor.full_name} added successfully.', 'success')
        return redirect(url_for('doctor.list_doctors'))

    return render_template('doctor_form.html', form=form, title='Add Doctor')


@doctor_bp.route('/edit/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin')
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        form.populate_obj(doctor)
        db.session.commit()
        flash('Doctor record updated successfully.', 'success')
        return redirect(url_for('doctor.list_doctors'))

    return render_template('doctor_form.html', form=form, title='Edit Doctor')


@doctor_bp.route('/delete/<int:doctor_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    flash('Doctor record deleted.', 'info')
    return redirect(url_for('doctor.list_doctors'))
