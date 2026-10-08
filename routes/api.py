from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import Patient, Doctor, Appointment, Consultation, Prescription, LabTest, Notification
from decorators import roles_required

api_bp = Blueprint('api', __name__, url_prefix='/api')


def create_notification(user_id, category, title, message):
    n = Notification(user_id=user_id, category=category, title=title, message=message)
    db.session.add(n)
    db.session.commit()
    return n


def notification_to_dict(n):
    return {
        'id': n.id, 'category': n.category, 'title': n.title,
        'message': n.message, 'is_read': n.is_read,
        'created_at': n.created_at.isoformat()
    }

from flask import request as flask_request


def log_audit(user_id, action, details=None):
    from models import AuditLog
    entry = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=flask_request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


@api_bp.route('/login', methods=['POST'])
def api_login():
    from flask_login import login_user
    from models import User

    data = request.get_json(force=True, silent=True) or {}
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user.id, 'full_name': user.full_name, 'role': user.role}
        }), 200
    else:
        return jsonify({'error': 'Invalid email or password'}), 401


def patient_to_dict(p):
    return {
        'id': p.id, 'display_id': p.display_id, 'full_name': p.full_name,
        'age': p.age, 'gender': p.gender, 'contact_number': p.contact_number,
        'blood_group': p.blood_group, 'mrn': p.mrn
    }


def doctor_to_dict(d):
    return {
        'id': d.id, 'full_name': d.full_name, 'specialization': d.specialization,
        'department': d.department, 'contact_number': d.contact_number, 'email': d.email
    }


def appointment_to_dict(a):
    return {
        'id': a.id, 'patient_id': a.patient_id, 'doctor_id': a.doctor_id,
        'patient_name': a.patient.full_name, 'doctor_name': a.doctor.full_name,
        'appointment_date': a.appointment_date.isoformat(),
        'appointment_time': a.appointment_time.strftime('%H:%M:%S'),
        'status': a.status
    }


def consultation_to_dict(c):
    return {
        'id': c.id, 'patient_id': c.patient_id, 'doctor_id': c.doctor_id,
        'consultation_date': c.consultation_date.isoformat(),
        'diagnosis': c.diagnosis, 'symptoms': c.symptoms, 'treatment': c.treatment
    }


def prescription_to_dict(pr):
    return {
        'id': pr.id, 'patient_id': pr.patient_id, 'doctor_id': pr.doctor_id,
        'medication_name': pr.medication_name, 'dosage': pr.dosage,
        'frequency': pr.frequency, 'prescribed_date': pr.prescribed_date.isoformat()
    }


def labtest_to_dict(lt):
    return {
        'id': lt.id, 'patient_id': lt.patient_id, 'test_name': lt.test_name,
        'category': lt.category, 'result': lt.result, 'status': lt.status,
        'test_date': lt.test_date.isoformat()
    }


@api_bp.route('/patients', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_patients():
    patients = Patient.query.all()
    return jsonify([patient_to_dict(p) for p in patients])


@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    return jsonify(patient_to_dict(p))


@api_bp.route('/patients', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def create_patient():
    data = request.get_json(force=True, silent=True) or {}
    required = ['full_name', 'age', 'gender', 'address']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    p = Patient(
        full_name=data['full_name'],
        age=data['age'],
        gender=data['gender'],
        contact_number=data.get('contact_number'),
        blood_group=data.get('blood_group'),
        address=data.get('address', 'Not provided')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(patient_to_dict(p)), 201


@api_bp.route('/patients/<int:patient_id>', methods=['PUT'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def update_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'full_name' in data:
        p.full_name = data['full_name']
    if 'age' in data:
        p.age = data['age']
    if 'gender' in data:
        p.gender = data['gender']
    if 'contact_number' in data:
        p.contact_number = data['contact_number']
    if 'blood_group' in data:
        p.blood_group = data['blood_group']

    db.session.commit()
    return jsonify(patient_to_dict(p)), 200


@api_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
@login_required
@roles_required('Admin')
def delete_patient(patient_id):
    p = Patient.query.get_or_404(patient_id)
    patient_name = p.full_name
    db.session.delete(p)
    db.session.commit()
    log_audit(current_user.id, 'delete_patient', f'Deleted patient: {patient_name} (id={patient_id})')
    return jsonify({'message': 'Patient deleted successfully'}), 200


@api_bp.route('/doctors', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_doctors():
    doctors = Doctor.query.all()
    return jsonify([doctor_to_dict(d) for d in doctors])


@api_bp.route('/doctors/<int:doctor_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_doctor(doctor_id):
    d = Doctor.query.get_or_404(doctor_id)
    return jsonify(doctor_to_dict(d))


@api_bp.route('/doctors', methods=['POST'])
@login_required
@roles_required('Admin')
def create_doctor():
    data = request.get_json(force=True, silent=True) or {}
    required = ['full_name', 'specialization', 'qualification']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    d = Doctor(
        full_name=data['full_name'],
        specialization=data['specialization'],
        qualification=data.get('qualification', 'Not specified'),
        department=data.get('department'),
        contact_number=data.get('contact_number'),
        email=data.get('email'),
        available_time=data.get('available_time', 'Not specified')
    )
    db.session.add(d)
    db.session.commit()
    return jsonify(doctor_to_dict(d)), 201


@api_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@login_required
@roles_required('Admin')
def update_doctor(doctor_id):
    d = Doctor.query.get_or_404(doctor_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'full_name' in data:
        d.full_name = data['full_name']
    if 'specialization' in data:
        d.specialization = data['specialization']
    if 'department' in data:
        d.department = data['department']
    if 'contact_number' in data:
        d.contact_number = data['contact_number']
    if 'email' in data:
        d.email = data['email']

    db.session.commit()
    return jsonify(doctor_to_dict(d)), 200


@api_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
@login_required
@roles_required('Admin')
def delete_doctor(doctor_id):
    d = Doctor.query.get_or_404(doctor_id)
    doctor_name = d.full_name
    db.session.delete(d)
    db.session.commit()
    log_audit(current_user.id, 'delete_doctor', f'Deleted doctor: {doctor_name} (id={doctor_id})')
    return jsonify({'message': 'Doctor deleted successfully'}), 200


# ---------- Appointments (new for Milestone 4 Day 3) ----------

@api_bp.route('/appointments', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    return jsonify([appointment_to_dict(a) for a in appointments])


@api_bp.route('/appointments/<int:appointment_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_appointment(appointment_id):
    a = Appointment.query.get_or_404(appointment_id)
    return jsonify(appointment_to_dict(a))


@api_bp.route('/appointments', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def create_appointment():
    data = request.get_json(force=True, silent=True) or {}
    required = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    try:
        appt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        appt_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'appointment_date must be YYYY-MM-DD, appointment_time must be HH:MM'}), 400

    a = Appointment(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        appointment_date=appt_date,
        appointment_time=appt_time,
        status=data.get('status', 'Scheduled')
    )
    db.session.add(a)
    db.session.commit()

    patient_user_id = a.patient.user_id
    if patient_user_id:
        create_notification(
            patient_user_id, 'appointment', 'Appointment Scheduled',
            f'Your appointment with Dr. {a.doctor.full_name} is set for {a.appointment_date}.'
        )

    return jsonify(appointment_to_dict(a)), 201


@api_bp.route('/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def update_appointment(appointment_id):
    a = Appointment.query.get_or_404(appointment_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'appointment_date' in data:
        try:
            a.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'appointment_date must be YYYY-MM-DD'}), 400
    if 'appointment_time' in data:
        try:
            a.appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'appointment_time must be HH:MM'}), 400
    if 'status' in data:
        a.status = data['status']

    db.session.commit()

    if data.get('status') == 'Cancelled' and a.patient.user_id:
        create_notification(
            a.patient.user_id, 'appointment', 'Appointment Cancelled',
            f'Your appointment with Dr. {a.doctor.full_name} on {a.appointment_date} was cancelled.'
        )

    return jsonify(appointment_to_dict(a)), 200


@api_bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
@roles_required('Admin')
def delete_appointment(appointment_id):
    a = Appointment.query.get_or_404(appointment_id)
    db.session.delete(a)
    db.session.commit()
    log_audit(current_user.id, 'delete_appointment', f'Deleted appointment id={appointment_id}')
    return jsonify({'message': 'Appointment deleted successfully'}), 200


@api_bp.route('/consultations', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_consultations():
    consultations = Consultation.query.all()
    return jsonify([consultation_to_dict(c) for c in consultations])


@api_bp.route('/consultations/<int:consultation_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_consultation(consultation_id):
    c = Consultation.query.get_or_404(consultation_id)
    return jsonify(consultation_to_dict(c))


@api_bp.route('/consultations', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor')
def create_consultation():
    data = request.get_json(force=True, silent=True) or {}
    required = ['patient_id', 'doctor_id', 'diagnosis']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    c = Consultation(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        diagnosis=data['diagnosis'],
        symptoms=data.get('symptoms'),
        treatment=data.get('treatment')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(consultation_to_dict(c)), 201


@api_bp.route('/consultations/<int:consultation_id>', methods=['PUT'])
@login_required
@roles_required('Admin', 'Doctor')
def update_consultation(consultation_id):
    c = Consultation.query.get_or_404(consultation_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'diagnosis' in data:
        c.diagnosis = data['diagnosis']
    if 'symptoms' in data:
        c.symptoms = data['symptoms']
    if 'treatment' in data:
        c.treatment = data['treatment']

    db.session.commit()
    return jsonify(consultation_to_dict(c)), 200


@api_bp.route('/consultations/<int:consultation_id>', methods=['DELETE'])
@login_required
@roles_required('Admin', 'Doctor')
def delete_consultation(consultation_id):
    c = Consultation.query.get_or_404(consultation_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Consultation deleted successfully'}), 200


@api_bp.route('/prescriptions', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_prescriptions():
    prescriptions = Prescription.query.all()
    return jsonify([prescription_to_dict(pr) for pr in prescriptions])

@api_bp.route('/prescriptions/<int:prescription_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_prescription(prescription_id):
    pr = Prescription.query.get_or_404(prescription_id)
    return jsonify(prescription_to_dict(pr)) 


@api_bp.route('/prescriptions', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor')
def create_prescription():
    data = request.get_json(force=True, silent=True) or {}
    required = ['patient_id', 'doctor_id', 'medication_name']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    pr = Prescription(
        patient_id=data['patient_id'],
        doctor_id=data['doctor_id'],
        medication_name=data['medication_name'],
        dosage=data.get('dosage'),
        frequency=data.get('frequency'),
        duration=data.get('duration')
    )
    db.session.add(pr)
    db.session.commit()

    patient_user_id = pr.patient.user_id
    if patient_user_id:
        create_notification(
            patient_user_id, 'prescription', 'New Prescription',
            f'A new prescription for {pr.medication_name} has been added.'
        )

    return jsonify(prescription_to_dict(pr)), 201


@api_bp.route('/prescriptions/<int:prescription_id>', methods=['PUT'])
@login_required
@roles_required('Admin', 'Doctor')
def update_prescription(prescription_id):
    pr = Prescription.query.get_or_404(prescription_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'medication_name' in data:
        pr.medication_name = data['medication_name']
    if 'dosage' in data:
        pr.dosage = data['dosage']
    if 'frequency' in data:
        pr.frequency = data['frequency']
    if 'duration' in data:
        pr.duration = data['duration']

    db.session.commit()
    return jsonify(prescription_to_dict(pr)), 200


@api_bp.route('/prescriptions/<int:prescription_id>', methods=['DELETE'])
@login_required
@roles_required('Admin', 'Doctor')
def delete_prescription(prescription_id):
    pr = Prescription.query.get_or_404(prescription_id)
    db.session.delete(pr)
    db.session.commit()
    return jsonify({'message': 'Prescription deleted successfully'}), 200


@api_bp.route('/laboratory', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_lab_tests():
    tests = LabTest.query.all()
    return jsonify([labtest_to_dict(lt) for lt in tests])


@api_bp.route('/laboratory/<int:test_id>', methods=['GET'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def get_lab_test(test_id):
    lt = LabTest.query.get_or_404(test_id)
    return jsonify(labtest_to_dict(lt))


@api_bp.route('/laboratory', methods=['POST'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def create_lab_test():
    data = request.get_json(force=True, silent=True) or {}
    required = ['patient_id', 'test_name']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    lt = LabTest(
        patient_id=data['patient_id'],
        test_name=data['test_name'],
        category=data.get('category'),
        result=data.get('result'),
        status=data.get('status', 'Pending')
    )
    db.session.add(lt)
    db.session.commit()

    patient_user_id = lt.patient.user_id
    if patient_user_id:
        create_notification(
            patient_user_id, 'lab', 'New Lab Test',
            f'A new lab test ({lt.test_name}) has been recorded.'
        )

    return jsonify(labtest_to_dict(lt)), 201

@api_bp.route('/laboratory/<int:test_id>', methods=['PUT'])
@login_required
@roles_required('Admin', 'Doctor', 'Nurse')
def update_lab_test(test_id):
    lt = LabTest.query.get_or_404(test_id)
    data = request.get_json(force=True, silent=True) or {}

    if 'result' in data:
        lt.result = data['result']
    if 'status' in data:
        lt.status = data['status']
    if 'category' in data:
        lt.category = data['category']

    db.session.commit()

    if 'result' in data and lt.patient.user_id:
        create_notification(
            lt.patient.user_id, 'lab', 'Lab Result Ready',
            f'Your result for {lt.test_name} is now available.'
        )

    return jsonify(labtest_to_dict(lt)), 200

@api_bp.route('/laboratory/<int:test_id>', methods=['DELETE'])
@login_required
@roles_required('Admin')
def delete_lab_test(test_id):
    lt = LabTest.query.get_or_404(test_id)
    db.session.delete(lt)
    db.session.commit()
    return jsonify({'message': 'Lab test deleted successfully'}), 200


@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([notification_to_dict(n) for n in notifications])


@api_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    n.is_read = True
    db.session.commit()
    return jsonify(notification_to_dict(n)), 200


@api_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    n = Notification.query.get_or_404(notification_id)
    if n.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    db.session.delete(n)
    db.session.commit()
    return jsonify({'message': 'Notification deleted successfully'}), 200