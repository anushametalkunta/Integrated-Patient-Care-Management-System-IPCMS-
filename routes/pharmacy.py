from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import or_

from extensions import db
from models import Medicine, Prescription, DispenseLog
from decorators import roles_required

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')


@pharmacy_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def index():
    q = request.args.get('q', '').strip()
    medicines = Medicine.query
    if q:
        like = f'%{q}%'
        medicines = medicines.filter(or_(
            Medicine.name.ilike(like),
            Medicine.category.ilike(like)
        ))
    medicines = medicines.order_by(Medicine.name.asc()).all()

    today = date.today()
    all_medicines = Medicine.query.all()
    stats = {
        'total': len(all_medicines),
        'available': len([m for m in all_medicines if m.status == 'Available']),
        'low_stock': len([m for m in all_medicines if m.status == 'Low Stock']),
        'expired': len([m for m in all_medicines if m.status == 'Expired']),
        'dispensed_today': DispenseLog.query.filter(
            db.func.date(DispenseLog.dispensed_at) == today
        ).count(),
    }

    pending_prescriptions = Prescription.query.order_by(Prescription.prescribed_date.desc()).limit(20).all()

    return render_template(
        'pharmacy.html',
        medicines=medicines,
        stats=stats,
        search=q,
        prescriptions=pending_prescriptions,
        active_page='pharmacy'
    )


@pharmacy_bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Nurse')
def add_medicine():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        manufacturer = request.form.get('manufacturer', '').strip()
        stock = request.form.get('stock', '0').strip()
        unit_price = request.form.get('unit_price', '0').strip()
        expiry_date = request.form.get('expiry_date', '').strip()

        if not name:
            flash('Medicine name is required.', 'danger')
            return redirect(url_for('pharmacy.add_medicine'))

        medicine = Medicine(
            name=name,
            category=category or None,
            manufacturer=manufacturer or None,
            stock=int(stock) if stock.isdigit() else 0,
            unit_price=float(unit_price) if unit_price else 0.0,
            expiry_date=date.fromisoformat(expiry_date) if expiry_date else None
        )
        db.session.add(medicine)
        db.session.commit()
        flash(f'Medicine "{medicine.name}" added to inventory.', 'success')
        return redirect(url_for('pharmacy.index'))

    return render_template('medicine_form.html', title='Add Medicine', medicine=None)


@pharmacy_bp.route('/update-stock/<int:medicine_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Nurse')
def update_stock(medicine_id):
    medicine = Medicine.query.get_or_404(medicine_id)
    new_stock = request.form.get('stock', '').strip()
    if new_stock.isdigit():
        medicine.stock = int(new_stock)
        db.session.commit()
        flash(f'Stock for {medicine.name} updated to {medicine.stock}.', 'success')
    else:
        flash('Invalid stock value.', 'danger')
    return redirect(url_for('pharmacy.index'))


@pharmacy_bp.route('/dispense/<int:prescription_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Nurse')
def dispense(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    medicine_id = request.form.get('medicine_id', '').strip()
    quantity = request.form.get('quantity', '').strip()

    medicine = Medicine.query.get(medicine_id) if medicine_id.isdigit() else None
    if not medicine:
        flash('Please select a valid medicine.', 'danger')
        return redirect(url_for('pharmacy.index'))

    if not quantity.isdigit() or int(quantity) <= 0:
        flash('Please enter a valid quantity.', 'danger')
        return redirect(url_for('pharmacy.index'))

    qty = int(quantity)
    if medicine.stock < qty:
        flash(f'Not enough stock for {medicine.name}. Available: {medicine.stock}.', 'danger')
        return redirect(url_for('pharmacy.index'))

    medicine.stock -= qty
    log = DispenseLog(prescription_id=prescription.id, medicine_id=medicine.id, quantity=qty)
    db.session.add(log)
    db.session.commit()
    flash(f'Dispensed {qty} x {medicine.name} for {prescription.patient.full_name}.', 'success')
    return redirect(url_for('pharmacy.index'))