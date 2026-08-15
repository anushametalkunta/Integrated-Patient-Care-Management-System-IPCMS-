# Integrated Patient Care Management System — Milestone 1 + 2

A Flask + MySQL hospital management system implementing core patient management,
secure user authentication, and Electronic Health Records (EHR), built to match
the Milestone 1 and Milestone 2 (Day 1) deliverables:

**Milestone 1**
- ✅ Secure user registration & login (passwords hashed, never stored in plain text)
- ✅ Role-based access for **Admin, Doctor, Nurse, Patient**
- ✅ Patient registration & profile management (view/edit)
- ✅ Doctor management module (add / view / edit / delete)
- ✅ Appointment booking & management
- ✅ Role-specific dashboards with live statistics
- ✅ MySQL database via Flask-SQLAlchemy (SQLite fallback for zero-setup local testing)
- ✅ HTML/CSS + Jinja templates

**Milestone 2 — Day 1: Electronic Health Records (EHR)**
- ✅ EHR database table linked to patients
- ✅ Store medical history, allergies, diagnoses, medications, and treatment notes
- ✅ EHR viewing page with patient summary
- ✅ Create and update EHR records (Admin, Doctor, Nurse)
- ✅ Patients can view their own medical record

## Project Structure

```
Integrated_Patient_Care/
│── app.py                 # App factory + entry point
│── config.py               # Configuration (reads .env)
│── extensions.py            # db, login_manager singletons
│── decorators.py            # @roles_required access control
│── forms.py                 # Flask-WTF forms
│── seed_data.py              # Optional: creates sample Admin/Doctor/Nurse/Patient
│── requirements.txt
│── .env.example
│── models/
│   └── __init__.py          # User, Patient, Doctor, Appointment, ElectronicHealthRecord
│── routes/
│   ├── auth.py               # register / login / logout
│   ├── dashboard.py          # role-based dashboards
│   ├── patient.py            # patient CRUD
│   ├── doctor.py             # doctor CRUD
│   ├── appointment.py        # book / list / cancel appointments
│   └── ehr.py                # electronic health records (view / create / update)
│── templates/                # Jinja2 + HTML/CSS templates
│── static/css/style.css
│── database/
│   └── schema.sql            # MySQL schema (optional manual setup)
```

## 1. Prerequisites

- Python 3.10+
- Git
- (Optional, for MySQL) MySQL Server + MySQL Workbench

## 2. Setup — Run Locally

```bash
# 1. Clone your repo (after you've pushed it — see Part 2 below)
git clone https://github.com/<your-username>/integrated-patient-care.git
cd integrated-patient-care

# 2. Create & activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and set a SECRET_KEY. Leave DATABASE_URL commented out to use SQLite
# instantly, or uncomment it and fill in your MySQL credentials (see Part 3).

# 5. Run the app (tables are auto-created on first run)
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

### Quickest way to see it working — load sample data

```bash
python seed_data.py
```

This creates one login for each role so you can test immediately:

| Role    | Email                 | Password    |
|---------|------------------------|-------------|
| Admin   | admin@hospital.com     | Admin@123   |
| Nurse   | nurse@hospital.com     | Nurse@123   |
| Doctor  | doctor@hospital.com    | Doctor@123  |
| Patient | patient@hospital.com   | Patient@123 |

Log in as each to see the role-specific dashboard, then try registering your own
account from the **Register** page (choose any role) to test the full flow.

## 3. Switching to MySQL (as required by the milestone)

1. Install MySQL Server and open MySQL Workbench (or the `mysql` CLI).
2. Create the database — either let SQLAlchemy do it automatically, or run the
   provided schema manually:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
3. In `.env`, uncomment and set:
   ```
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/patient_care_db
   ```
4. Re-run `python app.py` — Flask-SQLAlchemy will connect to MySQL and create any
   missing tables.

## 4. Testing Checklist (matches Day 7 deliverables)

- [ ] Register a user for each role (Admin, Doctor, Nurse, Patient)
- [ ] Log in with each role and confirm the correct dashboard appears
- [ ] Try an invalid password → confirm the error message shows
- [ ] As Admin, add/edit/delete a Doctor
- [ ] As Nurse/Patient, register a Patient profile
- [ ] Book an appointment (choose doctor, date, time) and confirm it appears in
      the Appointments list for both the patient and the doctor
- [ ] Cancel an appointment and confirm its status updates

### Milestone 2 — EHR (Day 1)

- [ ] Log in as Doctor/Nurse and open **EHR** from the navbar
- [ ] Create an EHR for a patient (medical history, allergies, diagnoses, medications)
- [ ] View the patient's medical record and confirm all fields display correctly
- [ ] Update the EHR and confirm the "Last updated" timestamp changes
- [ ] Log in as Patient and open **View My EHR** from the dashboard

## Part 2 — Push This Project to GitHub

```bash
# 1. From inside the Integrated_Patient_Care folder, initialize Git
git init

# 2. Stage and commit everything (the .gitignore already excludes venv/, .env, instance/)
git add .
git commit -m "Milestone 1: patient/doctor/appointment management with role-based auth"

# 3. Create a new EMPTY repository on GitHub (no README/license) named e.g.
#    "integrated-patient-care", then link it:
git branch -M main
git remote add origin https://github.com/<your-username>/integrated-patient-care.git

# 4. Push
git push -u origin main
```

After this, anyone (including you, on another machine) can get the project running with:

```bash
git clone https://github.com/<your-username>/integrated-patient-care.git
cd integrated-patient-care
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # then edit SECRET_KEY / DATABASE_URL
python app.py
```

### Making future changes

```bash
git add .
git commit -m "Describe what you changed"
git push
```

## Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2) — never
  stored or displayed in plain text.
- `.env` (containing `SECRET_KEY` and DB credentials) is git-ignored — never commit it.
- Routes are protected with `@login_required` and a custom `@roles_required(...)`
  decorator so, e.g., only Admins can add/delete doctors.
