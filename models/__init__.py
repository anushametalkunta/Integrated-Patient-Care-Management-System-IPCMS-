from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from utils import compute_bmi, patient_display_id, generate_mrn, bmi_category


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient_profile = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    aadhaar_number = db.Column(db.String(20), unique=True, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    email = db.Column(db.String(120), nullable=True)
    emergency_contact = db.Column(db.String(120), nullable=True)
    mrn = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='patient', cascade='all, delete-orphan')
    ehr = db.relationship(
        'ElectronicHealthRecord',
        backref='patient',
        uselist=False,
        cascade='all, delete-orphan'
    )
    consultations = db.relationship('Consultation', backref='patient', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='patient', cascade='all, delete-orphan')
    lab_tests = db.relationship('LabTest', backref='patient', cascade='all, delete-orphan')
    allergies = db.relationship('Allergy', backref='patient', cascade='all, delete-orphan')
    diagnosis_history = db.relationship('DiagnosisHistory', backref='patient', cascade='all, delete-orphan')

    @property
    def display_id(self):
        return patient_display_id(self.id)

    def ensure_mrn(self):
        if not self.mrn:
            self.mrn = generate_mrn(self.id)

    def __repr__(self):
        return f'<Patient {self.full_name}>'


class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    full_name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(120), nullable=False)
    qualification = db.Column(db.String(120), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    available_time = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship('Appointment', backref='doctor', cascade='all, delete-orphan')
    consultations = db.relationship('Consultation', backref='doctor', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='doctor', cascade='all, delete-orphan')
    lab_tests = db.relationship('LabTest', backref='doctor', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Doctor {self.full_name}>'


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='Scheduled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment #{self.id}>'


class ElectronicHealthRecord(db.Model):
    __tablename__ = 'electronic_health_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, unique=True)

    medical_summary = db.Column(db.Text, nullable=True)
    medical_history = db.Column(db.Text, nullable=True)
    allergies = db.Column(db.Text, nullable=True)
    chronic_diseases = db.Column(db.Text, nullable=True)
    diagnoses = db.Column(db.Text, nullable=True)
    medications = db.Column(db.Text, nullable=True)
    treatment_notes = db.Column(db.Text, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    bmi = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_vitals(self, height_cm=None, weight_kg=None):
        if height_cm is not None:
            self.height_cm = height_cm
        if weight_kg is not None:
            self.weight_kg = weight_kg
        self.bmi = compute_bmi(self.height_cm, self.weight_kg)

    @property
    def bmi_label(self):
        return bmi_category(self.bmi)

    def __repr__(self):
        return f'<EHR Patient #{self.patient_id}>'


class Consultation(db.Model):
    __tablename__ = 'consultations'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    consultation_date = db.Column(db.Date, nullable=False, default=date.today)
    symptoms = db.Column(db.Text, nullable=True)
    diagnosis = db.Column(db.String(255), nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Consultation #{self.id}>'


class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medication_name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(80), nullable=True)
    frequency = db.Column(db.String(80), nullable=True)
    duration = db.Column(db.String(80), nullable=True)
    prescribed_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prescription #{self.id}>'


class LabTest(db.Model):
    __tablename__ = 'lab_tests'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    test_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    result = db.Column(db.String(255), nullable=True)
    test_date = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(20), default='Completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LabTest #{self.id}>'


class DiagnosisHistory(db.Model):
    __tablename__ = 'diagnosis_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    diagnosis_date = db.Column(db.Date, nullable=False)
    diagnosis = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DiagnosisHistory #{self.id}>'


class Allergy(db.Model):
    __tablename__ = 'allergies'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    allergy_name = db.Column(db.String(120), nullable=False)
    reaction = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Allergy #{self.id}>'
class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    manufacturer = db.Column(db.String(120), nullable=True)
    stock = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    expiry_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def status(self):
        if self.expiry_date and self.expiry_date < date.today():
            return 'Expired'
        if self.stock <= 10:
            return 'Low Stock'
        return 'Available'

    def __repr__(self):
        return f'<Medicine {self.name}>'


class DispenseLog(db.Model):
    __tablename__ = 'dispense_logs'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescription = db.relationship('Prescription', backref='dispense_logs')
    medicine = db.relationship('Medicine', backref='dispense_logs')

    def __repr__(self):
        return f'<DispenseLog #{self.id}>'          
class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    bill_date = db.Column(db.Date, nullable=False, default=date.today)
    payment_method = db.Column(db.String(40), nullable=True)
    payment_status = db.Column(db.String(20), nullable=False, default='Pending')
    transaction_id = db.Column(db.String(80), nullable=True)
    paid_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='bills')
    items = db.relationship('BillItem', backref='bill', cascade='all, delete-orphan')

    @property
    def total_amount(self):
        return sum(item.amount for item in self.items)

    def __repr__(self):
        return f'<Bill #{self.id}>'


class BillItem(db.Model):
    __tablename__ = 'bill_items'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    service_type = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<BillItem {self.service_type}>'

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(40), nullable=False)  # 'appointment', 'lab', 'prescription', 'billing'
    title = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification #{self.id} for user {self.user_id}>'
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(80), nullable=False)  # e.g. 'delete_patient', 'login_failed'
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog #{self.id} {self.action}>'
class ApiLog(db.Model):
    __tablename__ = 'api_logs'

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(120), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ApiLog {self.method} {self.endpoint} {self.status_code}>'
class APICallLog(db.Model):
    __tablename__ = 'api_call_logs'

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(120), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    response_time_ms = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<APICallLog {self.method} {self.endpoint} {self.status_code}>'     

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=True)

    doctor_rating = db.Column(db.Integer, nullable=False)
    hospital_rating = db.Column(db.Integer, nullable=False)
    lab_rating = db.Column(db.Integer, nullable=False)
    pharmacy_rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='feedbacks')
    doctor = db.relationship('Doctor', backref='feedbacks')
    consultation = db.relationship('Consultation', backref=db.backref('feedback', uselist=False))

    @property
    def overall_rating(self):
        values = [self.doctor_rating, self.hospital_rating, self.lab_rating, self.pharmacy_rating]
        values = [v for v in values if v]
        return round(sum(values) / len(values), 1) if values else 0

    def __repr__(self):
        return f'<Feedback #{self.id} patient={self.patient_id}>'