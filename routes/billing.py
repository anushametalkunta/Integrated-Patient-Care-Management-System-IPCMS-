from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import Patient, Bill, BillItem, Consultation, LabTest, DispenseLog
from decorators import roles_required
from routes.api import create_notification

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')


@billing_bp.route('/')
@login_required
@roles_required('Admin', 'Nurse')
def index():
    q = request.args.get('q', '').strip()
    patients = []
    if q:
        like = f'%{q}%'
        patients = Patient.query.filter(or_(
            Patient.full_name.ilike(like),
            Patient.mrn.ilike(like),
            Patient.contact_number.ilike(like)
        )).all()

    bills = Bill.query.order_by(Bill.created_at.desc()).limit(20).all()

    return render_template(
        'billing.html',
        patients=patients,
        search=q,
        bills=bills,
        active_page='billing'
    )


@billing_bp.route('/create/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse')
def create_bill(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    consultation_fee = 500.0
    lab_charges = [{'name': t.test_name, 'amount': 300.0} for t in patient.lab_tests[-5:]]
    pharmacy_charges = []
    for log in DispenseLog.query.filter(
        DispenseLog.prescription.has(patient_id=patient.id)
    ).all():
        pharmacy_charges.append({
            'name': log.medicine.name,
            'amount': round(log.quantity * log.medicine.unit_price, 2)
        })
    if request.method == 'POST':
        payment_method = request.form.get('payment_method', '').strip()
        selected_items = request.form.getlist('item_selected')
        item_names = request.form.getlist('item_name')
        item_types = request.form.getlist('item_type')
        item_amounts = request.form.getlist('item_amount')

        bill = Bill(patient_id=patient.id, payment_method=payment_method or None)
        db.session.add(bill)
        db.session.flush()

        for i in selected_items:
            idx = int(i)
            db.session.add(BillItem(
                bill_id=bill.id,
                service_type=item_types[idx],
                description=item_names[idx],
                amount=float(item_amounts[idx])
            ))

        if not bill.items:
            db.session.rollback()
            flash('Please select at least one charge to bill.', 'danger')
            return redirect(url_for('billing.create_bill', patient_id=patient.id))

        if payment_method:
            bill.payment_status = 'Paid'
            bill.paid_date = date.today()
            bill.transaction_id = f'TXN{bill.id:06d}'

        db.session.commit()

        if patient.user_id:
            create_notification(
                patient.user_id, 'billing', 'New Invoice',
                f'A new invoice (#{bill.id}) totaling ₹{bill.total_amount:.2f} has been generated.'
            )

        flash(f'Invoice #{bill.id} generated for {patient.full_name}.', 'success')
        return redirect(url_for('billing.view_bill', bill_id=bill.id))

    return render_template(
        'billing_create.html',
        patient=patient,
        consultation_fee=consultation_fee,
        lab_charges=lab_charges,
        pharmacy_charges=pharmacy_charges,
        active_page='billing'
    )


@billing_bp.route('/invoice/<int:bill_id>')
@login_required
@roles_required('Admin', 'Nurse', 'Doctor', 'Patient')
def view_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    return render_template('invoice.html', bill=bill, active_page='billing')