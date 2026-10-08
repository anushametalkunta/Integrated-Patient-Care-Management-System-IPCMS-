"""
Milestone 4 - Day 3: System Integration end-to-end test.

Exercises the full workflow across modules in one continuous chain:
  Patient Registration -> EHR link -> Appointment Scheduling ->
  Consultation Management -> Prescription Management -> Notification System
  -> REST API read-back -> Role-based access control

Run with the Flask app already running (python app.py) in a separate
terminal, then in this project's venv:

    python test_integration.py

Uses the same test admin account as test_api.py (test@test.com).
"""

import requests

BASE_URL = 'http://127.0.0.1:5000'
session = requests.Session()

results = []


def check(name, condition):
    results.append((name, bool(condition)))
    status = 'PASS' if condition else 'FAIL'
    print(f'[{status}] {name}')


def run():
    # 1. Authenticate (Auth & Authorization module)
    r = session.post(f'{BASE_URL}/api/login', json={
        'email': 'test@test.com',
        'password': 'Test@1234'  # update if your test account uses a different password
    })
    check('Login via /api/login succeeds', r.status_code == 200)
    if r.status_code != 200:
        print('Cannot continue without a valid session - fix login credentials and re-run.')
        return

    # 2. Patient Registration
    r = session.post(f'{BASE_URL}/api/patients', json={
        'full_name': 'Integration Test Patient',
        'age': 30,
        'gender': 'Other',
        'address': '123 Test Street',
        'contact_number': '9990001111',
        'blood_group': 'O+'
    })
    check('Create patient via API', r.status_code == 201)
    patient = r.json() if r.status_code == 201 else None
    patient_id = patient['id'] if patient else None

    # 3. Confirm patient is readable back (Data Consistency / REST API)
    if patient_id:
        r = session.get(f'{BASE_URL}/api/patients/{patient_id}')
        check('Read back created patient', r.status_code == 200 and r.json()['full_name'] == 'Integration Test Patient')

    # 4. Get a doctor to schedule against
    r = session.get(f'{BASE_URL}/api/doctors')
    check('List doctors via API', r.status_code == 200)
    doctors = r.json() if r.status_code == 200 else []
    doctor_id = doctors[0]['id'] if doctors else None
    check('At least one doctor exists to schedule against', doctor_id is not None)

    appointment_id = None
    if patient_id and doctor_id:
        # 5. Appointment Scheduling
        r = session.post(f'{BASE_URL}/api/appointments', json={
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'appointment_date': '2026-12-01',
            'appointment_time': '10:00'
        })
        check('Create appointment via API', r.status_code == 201)
        appointment = r.json() if r.status_code == 201 else None
        appointment_id = appointment['id'] if appointment else None

    consultation_id = None
    if patient_id and doctor_id:
        # 6. Consultation Management
        r = session.post(f'{BASE_URL}/api/consultations', json={
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'diagnosis': 'Integration test diagnosis',
            'symptoms': 'None - automated test',
            'treatment': 'None - automated test'
        })
        check('Create consultation via API', r.status_code == 201)
        consultation = r.json() if r.status_code == 201 else None
        consultation_id = consultation['id'] if consultation else None

    if patient_id and doctor_id:
        # 7. Prescription Management (also triggers a Notification)
        r = session.post(f'{BASE_URL}/api/prescriptions', json={
            'patient_id': patient_id,
            'doctor_id': doctor_id,
            'medication_name': 'Integration Test Med',
            'dosage': '1 tablet',
            'frequency': 'Once daily',
            'duration': '5 days'
        })
        check('Create prescription via API', r.status_code == 201)

    # 8. Confirm the appointment shows up in the Appointment Report (cross-module read)
    r = session.get(f'{BASE_URL}/reports/appointments/export/csv')
    check('Appointment report export reachable', r.status_code == 200)

    # 9. Confirm dashboard loads with the new data folded in
    r = session.get(f'{BASE_URL}/dashboard')
    check('Dashboard loads after workflow', r.status_code == 200)

    # 10. Role-based access control: log out, log in as a non-Admin role if
    # available, confirm an Admin-only endpoint is blocked (403/401/302)
    session.get(f'{BASE_URL}/logout')
    r = session.post(f'{BASE_URL}/api/login', json={
        'email': 'nurse@hospital.com',
        'password': 'nurse123'  # update to your actual nurse test credentials
    })
    if r.status_code == 200:
        r2 = session.delete(f'{BASE_URL}/api/patients/{patient_id}' if patient_id else f'{BASE_URL}/api/patients/1')
        check('Nurse account blocked from Admin-only delete', r2.status_code in (401, 403))
    else:
        print('[SKIP] Nurse role-check skipped - update nurse credentials in this script to enable it')

    # Cleanup: log back in as admin and delete the test patient
    session.post(f'{BASE_URL}/api/login', json={'email': 'test@test.com', 'password': 'Test@1234'})
    if patient_id:
        session.delete(f'{BASE_URL}/api/patients/{patient_id}')

    # Summary
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f'\n{passed}/{total} checks passed')
    if passed == total:
        print('WORKFLOW INTEGRATION: PASSED')
    else:
        print('WORKFLOW INTEGRATION: FAILED - review the [FAIL] lines above')


if __name__ == '__main__':
    run()
