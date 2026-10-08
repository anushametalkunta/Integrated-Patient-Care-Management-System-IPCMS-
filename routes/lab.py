from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from extensions import db
from models import LabTest, Patient, Doctor
from forms import LabTestForm
from decorators import roles_required

lab_bp = Blueprint('lab', __name__, url_prefix='/laboratory')


def _populate_lab_choices(form):
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name).all()]
    form.doctor_id.choices = [(0, '— Not assigned —')] + [
        (d.id, f'Dr. {d.full_name}') for d in Doctor.query.order_by(Doctor.full_name).all()
    ]


@lab_bp.route('/')
@login_required
def list_tests():
    if current_user.role == 'Patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        tests = (
            LabTest.query.filter_by(patient_id=patient.id).order_by(LabTest.test_date.desc()).all()
            if patient else []
        )
    else:
        tests = LabTest.query.order_by(LabTest.test_date.desc()).all()

    return render_template('lab_tests.html', tests=tests)


@lab_bp.route('/request', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def request_test():
    form = LabTestForm()
    _populate_lab_choices(form)
    form.status.data = 'Requested'

    if current_user.role == 'Doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            form.doctor_id.choices = [(doctor.id, f'Dr. {doctor.full_name}')]
            form.doctor_id.data = doctor.id

    if form.validate_on_submit():
        doctor_id = form.doctor_id.data if form.doctor_id.data else None
        test = LabTest(
            patient_id=form.patient_id.data,
            doctor_id=doctor_id,
            test_name=form.test_name.data.strip(),
            category=form.category.data,
            test_date=form.test_date.data,
            result=(form.result.data or '').strip() or None,
            status=form.status.data,
        )
        db.session.add(test)
        db.session.commit()
        flash('Laboratory test request saved.', 'success')
        return redirect(url_for('lab.list_tests'))

    return render_template('lab_form.html', form=form, title='Request Lab Test')


@lab_bp.route('/<int:test_id>/result', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def update_result(test_id):
    test = LabTest.query.get_or_404(test_id)
    form = LabTestForm(obj=test)
    _populate_lab_choices(form)

    if form.validate_on_submit():
        test.patient_id = form.patient_id.data
        test.doctor_id = form.doctor_id.data if form.doctor_id.data else None
        test.test_name = form.test_name.data.strip()
        test.category = form.category.data
        test.test_date = form.test_date.data
        test.result = (form.result.data or '').strip() or None
        test.status = form.status.data
        db.session.commit()
        flash('Lab test result updated.', 'success')
        return redirect(url_for('lab.list_tests'))

    return render_template('lab_form.html', form=form, title='Update Lab Result', test=test)
