"""Populate database with sample data for IPCMS demo.
Run: python reset_db.py  then  python seed_data.py
"""
from datetime import date, timedelta

from app import create_app
from extensions import db
from models import (
    User, Doctor, Patient, ElectronicHealthRecord,
    Consultation, Prescription, LabTest, Allergy, DiagnosisHistory, Appointment
)
from utils import compute_bmi

app = create_app()

with app.app_context():
    db.create_all()

    def get_or_create_user(full_name, email, phone, password, role):
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(full_name=full_name, email=email, phone_number=phone, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            print(f'Created {role}: {email} / {password}')
        return user

    admin = get_or_create_user('System Admin', 'admin@hospital.com', '9999999999', 'Admin@123', 'Admin')
    get_or_create_user('Nurse Nancy', 'nurse@hospital.com', '9888888888', 'Nurse@123', 'Nurse')

    doc_user = get_or_create_user('Dr. John Smith', 'doctor@hospital.com', '9777777777', 'Doctor@123', 'Doctor')
    doctor = Doctor.query.filter_by(user_id=doc_user.id).first()
    if not doctor:
        doctor = Doctor(
            user_id=doc_user.id, full_name='John Smith', specialization='General Medicine',
            qualification='MBBS, MD', department='General', contact_number='9777777777',
            email='doctor@hospital.com', available_time='Mon-Fri, 9 AM - 2 PM'
        )
        db.session.add(doctor)
        db.session.commit()

    for name, spec, dept in [('Priya Sharma', 'Cardiology', 'Cardiology'), ('Rahul Verma', 'Pediatrics', 'Pediatrics')]:
        if not Doctor.query.filter_by(full_name=name).first():
            db.session.add(Doctor(
                full_name=name, specialization=spec, qualification='MBBS, MD',
                department=dept, contact_number='9000000000',
                email=f'{name.split()[0].lower()}@hospital.com', available_time='Mon-Sat, 10 AM - 4 PM'
            ))
    db.session.commit()
    doctor = Doctor.query.filter_by(user_id=doc_user.id).first()

    pat_user = get_or_create_user('Rahul Kumar', 'patient@hospital.com', '9666666666', 'Patient@123', 'Patient')
    patient = Patient.query.filter_by(user_id=pat_user.id).first()
    if not patient:
        patient = Patient(
            user_id=pat_user.id, full_name='Rahul Kumar', age=32, gender='Male',
            contact_number='9666666666', address='123 MG Road, Hyderabad', blood_group='O+',
            date_of_birth=date(1994, 3, 15), email='patient@hospital.com',
            emergency_contact='Priya Kumar — 9555555555'
        )
        db.session.add(patient)
        db.session.commit()
        patient.ensure_mrn()
        db.session.commit()

    extra_patients = [
        ('Ahmed Adams', 82, 'Female', 'B-', date(1944, 3, 21)),
        ('Priya Allen', 45, 'Female', 'A+', date(1981, 6, 10)),
        ('Robert Allen', 50, 'Male', 'O+', date(1976, 1, 5)),
    ]
    for name, age, gender, bg, dob in extra_patients:
        if not Patient.query.filter_by(full_name=name).first():
            p = Patient(
                full_name=name, age=age, gender=gender, contact_number='555-01000',
                address='City Hospital Area', blood_group=bg, date_of_birth=dob,
                email=f'{name.split()[0].lower()}@email.com'
            )
            db.session.add(p)
            db.session.commit()
            p.ensure_mrn()
    db.session.commit()
    patient = Patient.query.filter_by(user_id=pat_user.id).first()

    if patient and not ElectronicHealthRecord.query.filter_by(patient_id=patient.id).first():
        ehr = ElectronicHealthRecord(
            patient_id=patient.id,
            medical_summary='Hypertension under control. Seasonal asthma managed with inhaler.',
            medical_history='Seasonal asthma since childhood. Appendectomy in 2018.',
            chronic_diseases='Hypertension, Seasonal allergic rhinitis',
            allergies='Penicillin (rash), Peanuts (mild swelling)',
            diagnoses='Hypertension (controlled)',
            medications='Amlodipine 5mg daily, Salbutamol inhaler as needed',
            treatment_notes='Blood pressure stable. Follow-up in 3 months.',
            height_cm=175.0,
            weight_kg=73.0,
        )
        ehr.bmi = compute_bmi(ehr.height_cm, ehr.weight_kg)
        db.session.add(ehr)
        db.session.add(Allergy(patient_id=patient.id, allergy_name='Penicillin', reaction='Rash'))
        db.session.add(Allergy(patient_id=patient.id, allergy_name='Sea foods', reaction='Mild swelling'))
        db.session.add(DiagnosisHistory(
            patient_id=patient.id, diagnosis_date=date(2024, 6, 2),
            diagnosis='Hypertension', notes='Started on Amlodipine'
        ))
        db.session.commit()

    if doctor and patient and Consultation.query.count() == 0:
        for i in range(6):
            d = date.today().replace(day=1) - timedelta(days=30 * i)
            db.session.add(Consultation(
                patient_id=patient.id, doctor_id=doctor.id,
                consultation_date=d, diagnosis='General Checkup',
                notes=f'Routine visit month {i+1}'
            ))
        db.session.add(Prescription(
            patient_id=patient.id, doctor_id=doctor.id,
            medication_name='Amlodipine', dosage='5mg', frequency='Daily',
            prescribed_date=date.today()
        ))
        db.session.add(Prescription(
            patient_id=patient.id, doctor_id=doctor.id,
            medication_name='Paracetamol', dosage='500mg', frequency='As needed',
            prescribed_date=date.today() - timedelta(days=5)
        ))
        db.session.add(LabTest(
            patient_id=patient.id, doctor_id=doctor.id,
            test_name='Complete Blood Count', category='Blood',
            result='Normal', test_date=date.today(), status='Completed'
        ))
        db.session.add(LabTest(
            patient_id=patient.id, doctor_id=doctor.id,
            test_name='Chest X-Ray', category='Imaging',
            result='Clear', test_date=date.today() - timedelta(days=10), status='Completed'
        ))
        if not Appointment.query.filter_by(patient_id=patient.id).first():
            from datetime import time
            db.session.add(Appointment(
                patient_id=patient.id, doctor_id=doctor.id,
                appointment_date=date.today() + timedelta(days=7),
                appointment_time=time(10, 0), status='Scheduled'
            ))
        db.session.commit()
        print('Created consultations, prescriptions, lab tests, and sample appointment.')

    print('\nSample data ready!')
    print('Login: admin@hospital.com / Admin@123')
    print('       doctor@hospital.com / Doctor@123')
    print('       nurse@hospital.com / Nurse@123')
    print('       patient@hospital.com / Patient@123')
