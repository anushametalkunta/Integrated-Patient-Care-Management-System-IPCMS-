import csv
import io
from datetime import datetime, date
from collections import defaultdict, Counter

from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from sqlalchemy import or_

from models import (
    Patient, Doctor, Appointment, Consultation, Prescription,
    LabTest, User, Bill, BillItem
)
from decorators import roles_required

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


# ---------- existing routes (unchanged) ----------

@reports_bp.route('/')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def index():
    q = request.args.get('q', '').strip()
    patients = Patient.query
    if q:
        like = f'%{q}%'
        patients = patients.filter(or_(
            Patient.full_name.ilike(like),
            Patient.mrn.ilike(like),
            Patient.contact_number.ilike(like)
        ))
    patients = patients.order_by(Patient.created_at.desc()).all()
    return render_template(
        'reports.html',
        patients=patients,
        stats={
            'patients': Patient.query.count(),
            'consultations': Consultation.query.count(),
            'prescriptions': Prescription.query.count(),
            'lab_tests': LabTest.query.count(),
            'users': User.query.count(),
        },
        search=q,
        active_page='reports'
    )


@reports_bp.route('/excel/<int:patient_id>')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def export_excel(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Patient ID', patient.display_id])
    writer.writerow(['MRN', patient.mrn or ''])
    writer.writerow(['Name', patient.full_name])
    writer.writerow(['Gender', patient.gender])
    writer.writerow(['Blood Group', patient.blood_group])
    writer.writerow(['Contact', patient.contact_number])
    if patient.ehr:
        writer.writerow(['Medical Summary', patient.ehr.medical_summary or ''])
        writer.writerow(['Allergies', patient.ehr.allergies or ''])
        writer.writerow(['Diagnoses', patient.ehr.diagnoses or ''])
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=patient_{patient.id}.csv'}
    )


# ---------- shared export helpers ----------

def _csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )


def _pdf_response(filename, title, headers, rows):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles['Title']), Spacer(1, 12)]

    table_data = [headers] + [[str(cell) for cell in row] for row in rows]
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    doc.build(story)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
    )


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


# ---------- Appointment report ----------

def _appointment_data():
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))
    doctor_id = request.args.get('doctor_id', type=int)
    status = request.args.get('status', '').strip()

    query = Appointment.query
    if start:
        query = query.filter(Appointment.appointment_date >= start)
    if end:
        query = query.filter(Appointment.appointment_date <= end)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if status:
        query = query.filter(Appointment.status == status)

    appts = query.order_by(Appointment.appointment_date.desc()).all()
    headers = ['Date', 'Time', 'Patient', 'Doctor', 'Department', 'Status']
    rows = [
        [a.appointment_date, a.appointment_time, a.patient.full_name,
         a.doctor.full_name, a.doctor.department, a.status]
        for a in appts
    ]
    return headers, rows, appts


@reports_bp.route('/appointments')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def appointments_report():
    headers, rows, appts = _appointment_data()
    return render_template(
        'report_view.html',
        title='Appointment Report',
        report_key='appointments',
        headers=headers,
        rows=rows,
        doctors=Doctor.query.order_by(Doctor.full_name).all(),
        statuses=['Scheduled', 'Completed', 'Cancelled'],
        active_page='reports'
    )


@reports_bp.route('/appointments/export/<fmt>')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def export_appointments(fmt):
    headers, rows, _ = _appointment_data()
    if fmt == 'pdf':
        return _pdf_response('appointment_report', 'Appointment Report', headers, rows)
    return _csv_response('appointment_report', headers, rows)


# ---------- Consultation report ----------

def _consultation_data():
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))
    doctor_id = request.args.get('doctor_id', type=int)

    query = Consultation.query
    if start:
        query = query.filter(Consultation.consultation_date >= start)
    if end:
        query = query.filter(Consultation.consultation_date <= end)
    if doctor_id:
        query = query.filter(Consultation.doctor_id == doctor_id)

    consults = query.order_by(Consultation.consultation_date.desc()).all()
    headers = ['Date', 'Patient', 'Doctor', 'Diagnosis', 'Follow-up']
    rows = [
        [c.consultation_date, c.patient.full_name, c.doctor.full_name,
         c.diagnosis or '-', c.follow_up_date or '-']
        for c in consults
    ]
    return headers, rows, consults


@reports_bp.route('/consultations')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def consultations_report():
    headers, rows, _ = _consultation_data()
    return render_template(
        'report_view.html',
        title='Consultation Report',
        report_key='consultations',
        headers=headers,
        rows=rows,
        doctors=Doctor.query.order_by(Doctor.full_name).all(),
        statuses=None,
        active_page='reports'
    )


@reports_bp.route('/consultations/export/<fmt>')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def export_consultations(fmt):
    headers, rows, _ = _consultation_data()
    if fmt == 'pdf':
        return _pdf_response('consultation_report', 'Consultation Report', headers, rows)
    return _csv_response('consultation_report', headers, rows)


# ---------- Prescription report ----------

def _prescription_data():
    start = _parse_date(request.args.get('start_date'))
    end = _parse_date(request.args.get('end_date'))
    doctor_id = request.args.get('doctor_id', type=int)

    query = Prescription.query
    if start:
        query = query.filter(Prescription.prescribed_date >= start)
    if end:
        query = query.filter(Prescription.prescribed_date <= end)
    if doctor_id:
        query = query.filter(Prescription.doctor_id == doctor_id)

    rx = query.order_by(Prescription.prescribed_date.desc()).all()
    headers = ['Date', 'Patient', 'Doctor', 'Medication', 'Dosage', 'Frequency', 'Duration']
    rows = [
        [p.prescribed_date, p.patient.full_name, p.doctor.full_name,
         p.medication_name, p.dosage or '-', p.frequency or '-', p.duration or '-']
        for p in rx
    ]
    return headers, rows, rx


@reports_bp.route('/prescriptions')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def prescriptions_report():
    headers, rows, _ = _prescription_data()
    return render_template(
        'report_view.html',
        title='Prescription Report',
        report_key='prescriptions',
        headers=headers,
        rows=rows,
        doctors=Doctor.query.order_by(Doctor.full_name).all(),
        statuses=None,
        active_page='reports'
    )


@reports_bp.route('/prescriptions/export/<fmt>')
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def export_prescriptions(fmt):
    headers, rows, _ = _prescription_data()
    if fmt == 'pdf':
        return _pdf_response('prescription_report', 'Prescription Report', headers, rows)
    return _csv_response('prescription_report', headers, rows)


# ---------- Doctor performance report ----------

def _doctor_performance_data():
    doctors = Doctor.query.order_by(Doctor.full_name).all()
    headers = ['Doctor', 'Department', 'Total Appointments', 'Completed', 'Cancelled', 'Consultations', 'Prescriptions']
    rows = []
    for d in doctors:
        appts = d.appointments
        completed = sum(1 for a in appts if a.status == 'Completed')
        cancelled = sum(1 for a in appts if a.status == 'Cancelled')
        rows.append([
            d.full_name, d.department, len(appts), completed, cancelled,
            len(d.consultations), len(d.prescriptions)
        ])
    return headers, rows


@reports_bp.route('/doctor-performance')
@login_required
@roles_required('Admin')
def doctor_performance_report():
    headers, rows = _doctor_performance_data()
    return render_template(
        'report_view.html',
        title='Doctor Performance Report',
        report_key='doctor-performance',
        headers=headers,
        rows=rows,
        doctors=None,
        statuses=None,
        active_page='reports'
    )


@reports_bp.route('/doctor-performance/export/<fmt>')
@login_required
@roles_required('Admin')
def export_doctor_performance(fmt):
    headers, rows = _doctor_performance_data()
    if fmt == 'pdf':
        return _pdf_response('doctor_performance_report', 'Doctor Performance Report', headers, rows)
    return _csv_response('doctor_performance_report', headers, rows)


# ---------- Department-wise report ----------

def _department_data():
    doctors = Doctor.query.all()
    by_dept = defaultdict(lambda: {'doctors': 0, 'appointments': 0, 'consultations': 0})
    for d in doctors:
        by_dept[d.department]['doctors'] += 1
        by_dept[d.department]['appointments'] += len(d.appointments)
        by_dept[d.department]['consultations'] += len(d.consultations)

    headers = ['Department', 'Doctors', 'Total Appointments', 'Total Consultations']
    rows = [
        [dept, v['doctors'], v['appointments'], v['consultations']]
        for dept, v in sorted(by_dept.items())
    ]
    return headers, rows


@reports_bp.route('/department')
@login_required
@roles_required('Admin')
def department_report():
    headers, rows = _department_data()
    return render_template(
        'report_view.html',
        title='Department-wise Report',
        report_key='department',
        headers=headers,
        rows=rows,
        doctors=None,
        statuses=None,
        active_page='reports'
    )


@reports_bp.route('/department/export/<fmt>')
@login_required
@roles_required('Admin')
def export_department(fmt):
    headers, rows = _department_data()
    if fmt == 'pdf':
        return _pdf_response('department_report', 'Department-wise Report', headers, rows)
    return _csv_response('department_report', headers, rows)


# ---------- Monthly hospital report ----------

def _monthly_hospital_data():
    patients = Patient.query.all()
    appts = Appointment.query.all()
    consults = Consultation.query.all()
    paid_items = (
        BillItem.query.join(Bill, Bill.id == BillItem.bill_id)
        .filter(Bill.payment_status == 'Paid').all()
    )

    months = set()
    patient_counts = Counter()
    appt_counts = Counter()
    consult_counts = Counter()
    revenue_by_month = Counter()

    for p in patients:
        key = p.created_at.strftime('%Y-%m') if p.created_at else None
        if key:
            patient_counts[key] += 1
            months.add(key)
    for a in appts:
        key = a.appointment_date.strftime('%Y-%m')
        appt_counts[key] += 1
        months.add(key)
    for c in consults:
        key = c.consultation_date.strftime('%Y-%m')
        consult_counts[key] += 1
        months.add(key)
    for item in paid_items:
        key = item.bill.bill_date.strftime('%Y-%m')
        revenue_by_month[key] += item.amount
        months.add(key)

    headers = ['Month', 'New Patients', 'Appointments', 'Consultations', 'Revenue']
    rows = [
        [m, patient_counts.get(m, 0), appt_counts.get(m, 0),
         consult_counts.get(m, 0), f'{revenue_by_month.get(m, 0):.2f}']
        for m in sorted(months)
    ]
    return headers, rows


@reports_bp.route('/monthly')
@login_required
@roles_required('Admin')
def monthly_report():
    headers, rows = _monthly_hospital_data()
    return render_template(
        'report_view.html',
        title='Monthly Hospital Report',
        report_key='monthly',
        headers=headers,
        rows=rows,
        doctors=None,
        statuses=None,
        active_page='reports'
    )


@reports_bp.route('/monthly/export/<fmt>')
@login_required
@roles_required('Admin')
def export_monthly(fmt):
    headers, rows = _monthly_hospital_data()
    if fmt == 'pdf':
        return _pdf_response('monthly_hospital_report', 'Monthly Hospital Report', headers, rows)
    return _csv_response('monthly_hospital_report', headers, rows)