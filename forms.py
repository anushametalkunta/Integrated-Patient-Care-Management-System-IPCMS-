from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, DateField, TimeField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional


class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match')]
    )
    role = SelectField('User Role', choices=[
        ('Patient', 'Patient'), ('Doctor', 'Doctor'), ('Nurse', 'Nurse'), ('Admin', 'Admin')
    ], validators=[DataRequired()])


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class PatientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=130)])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other'), ('Not Specified', 'Not Specified')
    ], validators=[DataRequired()])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(max=20)])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    blood_group = SelectField('Blood Group', choices=[
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('N/A', 'N/A')
    ], validators=[DataRequired()])
    aadhaar_number = StringField('Aadhaar Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=120)])


class DoctorForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=120)])
    qualification = StringField('Qualification', validators=[DataRequired(), Length(max=120)])
    department = StringField('Department', validators=[DataRequired(), Length(max=120)])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    available_time = StringField('Available Time', validators=[DataRequired(), Length(max=120)])


class AppointmentForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired()])


class EHRForm(FlaskForm):
    medical_summary = TextAreaField('Medical Summary', validators=[Optional(), Length(max=5000)],
                                    render_kw={'rows': 3})
    medical_history = TextAreaField('Medical History', validators=[Optional(), Length(max=5000)],
                                    render_kw={'rows': 3})
    chronic_diseases = TextAreaField('Chronic Diseases', validators=[Optional(), Length(max=2000)],
                                     render_kw={'rows': 2})
    allergies = TextAreaField('Allergies (text)', validators=[Optional(), Length(max=2000)],
                              render_kw={'rows': 2})
    diagnoses = TextAreaField('Diagnoses (text)', validators=[Optional(), Length(max=2000)],
                              render_kw={'rows': 2})
    medications = TextAreaField('Medications', validators=[Optional(), Length(max=2000)],
                                render_kw={'rows': 2})
    treatment_notes = TextAreaField('Treatment Notes', validators=[Optional(), Length(max=5000)],
                                  render_kw={'rows': 3})
    height_cm = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=30, max=300)])
    weight_kg = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=1, max=500)])


class ConsultationForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    consultation_date = DateField('Consultation Date', validators=[DataRequired()])
    diagnosis = StringField('Diagnosis', validators=[Optional(), Length(max=255)])
    follow_up_date = DateField('Follow-up Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)], render_kw={'rows': 3})


class PrescriptionForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    medication_name = StringField('Medication', validators=[DataRequired(), Length(max=120)])
    dosage = StringField('Dosage', validators=[Optional(), Length(max=80)])
    frequency = StringField('Frequency', validators=[Optional(), Length(max=80)])
    prescribed_date = DateField('Prescribed Date', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)], render_kw={'rows': 2})


class LabTestForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[Optional()])
    test_name = StringField('Test Name', validators=[DataRequired(), Length(max=120)])
    category = SelectField('Category', choices=[
        ('Blood', 'Blood'), ('Urine', 'Urine'), ('Imaging', 'Imaging'),
        ('Pathology', 'Pathology'), ('Other', 'Other')
    ], validators=[DataRequired()])
    result = StringField('Result', validators=[Optional(), Length(max=255)])
    test_date = DateField('Test Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])


class AllergyForm(FlaskForm):
    allergy_name = StringField('Allergy', validators=[DataRequired(), Length(max=120)])
    reaction = StringField('Reaction', validators=[Optional(), Length(max=255)])


class DiagnosisForm(FlaskForm):
    diagnosis_date = DateField('Date', validators=[DataRequired()])
    diagnosis = StringField('Diagnosis', validators=[DataRequired(), Length(max=255)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)], render_kw={'rows': 2})
