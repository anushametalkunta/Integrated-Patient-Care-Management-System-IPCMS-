import requests

BASE_URL = "http://127.0.0.1:5000"

# 1. Test login
login_payload = {
    "email": "test@test.com",
    "password": "Test1234"
}
session = requests.Session()
resp = session.post(f"{BASE_URL}/api/login", json=login_payload)
print("LOGIN STATUS:", resp.status_code)
print("LOGIN RESPONSE TEXT:", resp.text)

# 2. Test prescription endpoint (adjust path/id as needed)
resp2 = session.get(f"{BASE_URL}/api/prescriptions/3")
print("PRESCRIPTION STATUS:", resp2.status_code)
print("PRESCRIPTION RESPONSE:", resp2.text)
resp3 = session.get(f"{BASE_URL}/api/prescriptions")
print("PRESCRIPTION LIST STATUS:", resp3.status_code)
print("PRESCRIPTION LIST RESPONSE:", resp3.text)

# 3. Test update (PUT) - update prescription 5 (Paracetamol)
update_payload = {
    "dosage": "2 Tablets",
    "frequency": "Once daily"
}
resp4 = session.put(f"{BASE_URL}/api/prescriptions/5", json=update_payload)
print("UPDATE STATUS:", resp4.status_code)
print("UPDATE RESPONSE:", resp4.text)
# 4. Create a throwaway prescription, then delete it
new_rx = {
    "patient_id": 4,
    "doctor_id": 3,
    "medication_name": "Test Medicine (delete me)",
    "dosage": "1",
    "frequency": "Once"
}
resp5 = session.post(f"{BASE_URL}/api/prescriptions", json=new_rx)
print("CREATE STATUS:", resp5.status_code)
print("CREATE RESPONSE:", resp5.text)

new_id = resp5.json().get("id")

resp6 = session.delete(f"{BASE_URL}/api/prescriptions/{new_id}")
print("DELETE STATUS:", resp6.status_code)
print("DELETE RESPONSE:", resp6.text)
# 5. Test patient CRUD - create, update, delete a throwaway patient
new_patient = {
    "full_name": "Test Patient (delete me)",
    "age": 30,
    "gender": "Other",
    "contact_number": "0000000000",
    "blood_group": "O+",
    "address": "123 Test Street"
}
resp7 = session.post(f"{BASE_URL}/api/patients", json=new_patient)
print("PATIENT CREATE STATUS:", resp7.status_code)
print("PATIENT CREATE RESPONSE:", resp7.text)

patient_id = resp7.json().get("id")

update_patient_payload = {"age": 31}
resp8 = session.put(f"{BASE_URL}/api/patients/{patient_id}", json=update_patient_payload)
print("PATIENT UPDATE STATUS:", resp8.status_code)
print("PATIENT UPDATE RESPONSE:", resp8.text)

resp9 = session.delete(f"{BASE_URL}/api/patients/{patient_id}")
print("PATIENT DELETE STATUS:", resp9.status_code)
print("PATIENT DELETE RESPONSE:", resp9.text)
# 6. Test doctor CRUD - create, update, delete a throwaway doctor
new_doctor = {
    "full_name": "Dr. Test (delete me)",
    "specialization": "General Medicine",
    "qualification": "MBBS",
    "department": "General",
    "contact_number": "1111111111",
    "email": "drtest@test.com",
    "available_time": "9 AM - 5 PM"
}
resp10 = session.post(f"{BASE_URL}/api/doctors", json=new_doctor)
print("DOCTOR CREATE STATUS:", resp10.status_code)
print("DOCTOR CREATE RESPONSE:", resp10.text)

doctor_id = resp10.json().get("id")

update_doctor_payload = {"department": "Cardiology"}
resp11 = session.put(f"{BASE_URL}/api/doctors/{doctor_id}", json=update_doctor_payload)
print("DOCTOR UPDATE STATUS:", resp11.status_code)
print("DOCTOR UPDATE RESPONSE:", resp11.text)

resp12 = session.delete(f"{BASE_URL}/api/doctors/{doctor_id}")
print("DOCTOR DELETE STATUS:", resp12.status_code)
print("DOCTOR DELETE RESPONSE:", resp12.text)
# 7. Test consultation CRUD - create, update, delete a throwaway consultation
new_consultation = {
    "patient_id": 4,
    "doctor_id": 3,
    "diagnosis": "Test diagnosis (delete me)",
    "symptoms": "Test symptoms",
    "treatment": "Test treatment"
}
resp13 = session.post(f"{BASE_URL}/api/consultations", json=new_consultation)
print("CONSULTATION CREATE STATUS:", resp13.status_code)
print("CONSULTATION CREATE RESPONSE:", resp13.text)

consultation_id = resp13.json().get("id")

update_consultation_payload = {"treatment": "Updated treatment"}
resp14 = session.put(f"{BASE_URL}/api/consultations/{consultation_id}", json=update_consultation_payload)
print("CONSULTATION UPDATE STATUS:", resp14.status_code)
print("CONSULTATION UPDATE RESPONSE:", resp14.text)

resp15 = session.delete(f"{BASE_URL}/api/consultations/{consultation_id}")
print("CONSULTATION DELETE STATUS:", resp15.status_code)
print("CONSULTATION DELETE RESPONSE:", resp15.text) 
# 8. Test laboratory CRUD - create, update, delete a throwaway lab test
new_lab_test = {
    "patient_id": 4,
    "test_name": "Test Blood Panel (delete me)",
    "category": "Blood",
    "status": "Pending"
}
resp16 = session.post(f"{BASE_URL}/api/laboratory", json=new_lab_test)
print("LAB CREATE STATUS:", resp16.status_code)
print("LAB CREATE RESPONSE:", resp16.text)

lab_id = resp16.json().get("id")

update_lab_payload = {"status": "Completed", "result": "Normal"}
resp17 = session.put(f"{BASE_URL}/api/laboratory/{lab_id}", json=update_lab_payload)
print("LAB UPDATE STATUS:", resp17.status_code)
print("LAB UPDATE RESPONSE:", resp17.text)

resp18 = session.delete(f"{BASE_URL}/api/laboratory/{lab_id}")
print("LAB DELETE STATUS:", resp18.status_code)
print("LAB DELETE RESPONSE:", resp18.text)
# 9. Test notifications - create a prescription, check notification appears
new_rx2 = {
    "patient_id": 5,
    "doctor_id": 3,
    "medication_name": "Notification Test Med"
}
resp19 = session.post(f"{BASE_URL}/api/prescriptions", json=new_rx2)
print("RX FOR NOTIF STATUS:", resp19.status_code)

resp20 = session.get(f"{BASE_URL}/api/notifications")
print("NOTIFICATIONS STATUS:", resp20.status_code)
print("NOTIFICATIONS RESPONSE:", resp20.text)