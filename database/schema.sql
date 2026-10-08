-- Integrated Patient Care Management System
-- MySQL schema (Flask-SQLAlchemy will also auto-create these tables via db.create_all())

CREATE DATABASE IF NOT EXISTS patient_care_db;
USE patient_care_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(120) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    address VARCHAR(255) NOT NULL,
    blood_group VARCHAR(5) NOT NULL,
    date_of_birth DATE,
    email VARCHAR(120),
    emergency_contact VARCHAR(120),
    mrn VARCHAR(20) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(120) NOT NULL,
    specialization VARCHAR(120) NOT NULL,
    qualification VARCHAR(120) NOT NULL,
    department VARCHAR(120) NOT NULL,
    contact_number VARCHAR(20) NOT NULL,
    email VARCHAR(120) NOT NULL,
    available_time VARCHAR(120) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS electronic_health_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL UNIQUE,
    medical_summary TEXT,
    medical_history TEXT,
    allergies TEXT,
    chronic_diseases TEXT,
    diagnoses TEXT,
    medications TEXT,
    treatment_notes TEXT,
    height_cm FLOAT,
    weight_kg FLOAT,
    bmi FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS consultations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    consultation_date DATE NOT NULL,
    symptoms TEXT,
    diagnosis VARCHAR(255),
    treatment TEXT,
    follow_up_date DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    medication_name VARCHAR(120) NOT NULL,
    dosage VARCHAR(80),
    frequency VARCHAR(80),
    duration VARCHAR(80),
    prescribed_date DATE NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lab_tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT,
    test_name VARCHAR(120) NOT NULL,
    category VARCHAR(80) NOT NULL,
    result VARCHAR(255),
    test_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS diagnosis_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    diagnosis_date DATE NOT NULL,
    diagnosis VARCHAR(255) NOT NULL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS allergies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    allergy_name VARCHAR(120) NOT NULL,
    reaction VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);
