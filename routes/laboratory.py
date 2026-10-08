from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import LabTest, Patient, Doctor
from forms import LabTestForm
from decorators import roles_required

laboratory_bp = Blueprint('laboratory', __name__, url_prefix='/laboratory')


def _populate_form_choices(form):
    form.patient_id.choices = [(p.id, p.full_name) for p in Patient.query.order_by(Patient.full_name)]
    form.doctor_id.choices = [(0, '— None —')] + [
        (d.id, d.full_name) for d in Doctor.query.order_by(Doctor.full_name)
    ]


@laboratory_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def list_tests():
    search = request.args.get('q', '').strip()
    query = LabTest.query.join(Patient)
    if search:
        like = f'%{search}%'
        query = query.filter(or_(Patient.full_name.ilike(like), LabTest.test_name.ilike(like)))
    tests = query.order_by(LabTest.test_date.desc()).all()
    return render_template(
        'laboratory.html',
        tests=tests,
        total=len(tests),
        search=search,
        active_page='laboratory'
    )


@laboratory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def add_test():
    form = LabTestForm()
    _populate_form_choices(form)
    if form.validate_on_submit():
        doctor_id = form.doctor_id.data if form.doctor_id.data else None
        db.session.add(LabTest(
            patient_id=form.patient_id.data,
            doctor_id=doctor_id,
            test_name=form.test_name.data.strip(),
            category=form.category.data,
            result=(form.result.data or '').strip() or None,
            test_date=form.test_date.data,
            status=form.status.data
        ))
        db.session.commit()
        flash('Lab test record added.', 'success')
        return redirect(url_for('laboratory.list_tests'))
    return render_template('lab_form.html', form=form, title='Add Lab Test', active_page='laboratory')
