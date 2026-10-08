"""
Milestone 4 - Day 7: Final Smoke Test

Hits every page and module built across Days 1-6 in one pass, as final
evidence that the whole system works together before calling Milestone
4 complete.

Run with the Flask app already running (python app.py) in a separate
terminal, then:

    python final_smoke_test.py
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://127.0.0.1:5000'
session = requests.Session()

ADMIN_EMAIL = 'test@test.com'
ADMIN_PASSWORD = 'Test@1234'

results = []


def check(name, condition):
    results.append((name, bool(condition)))
    status = 'PASS' if condition else 'FAIL'
    print(f'[{status}] {name}')


def get_ok(path, roles_note=''):
    r = session.get(f'{BASE_URL}{path}')
    check(f'{path} loads' + (f' ({roles_note})' if roles_note else ''), r.status_code == 200)


def run():
    r = session.post(f'{BASE_URL}/api/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})
    check('Admin login succeeds', r.status_code == 200)
    if r.status_code != 200:
        print('Cannot continue without a valid session.')
        return

    print('\n--- Day 1: Dashboard & Analytics ---')
    get_ok('/dashboard')

    print('\n--- Day 2: Administrative Reporting ---')
    get_ok('/reports/')
    get_ok('/reports/appointments')
    get_ok('/reports/consultations')
    get_ok('/reports/prescriptions')
    get_ok('/reports/doctor-performance')
    get_ok('/reports/department')
    get_ok('/reports/monthly')

    print('\n--- Day 3: System Integration ---')
    get_ok('/system-integration/')
    get_ok('/api/patients')
    get_ok('/api/doctors')
    get_ok('/api/appointments')
    get_ok('/api/consultations')
    get_ok('/api/prescriptions')

    print('\n--- Day 4: Testing & QA ---')
    get_ok('/testing-qa/')

    print('\n--- Day 5: Dashboard Analytics (already covered above) ---')

    print('\n--- Day 6: Patient Feedback ---')
    get_ok('/feedback/')

    print('\n--- Core clinical modules ---')
    get_ok('/patients/')
    get_ok('/doctors/')
    get_ok('/consultations/')
    get_ok('/prescriptions/')

    print('\n--- Security spot-check ---')
    anon = requests.Session()
    r = anon.get(f'{BASE_URL}/dashboard', allow_redirects=False)
    check('Unauthenticated access still blocked', r.status_code in (302, 401, 403))

    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f'\n{passed}/{total} checks passed')
    if passed == total:
        print('FINAL SMOKE TEST: ALL SYSTEMS GO - MILESTONE 4 READY')
    else:
        print('FINAL SMOKE TEST: SOME CHECKS FAILED - review [FAIL] lines above')
    with open('smoke_test_results.json', 'w') as f:
        json.dump({
            'run_at': datetime.utcnow().isoformat(),
            'passed': passed,
            'total': total,
            'results': [{'name': name, 'passed': ok} for name, ok in results]
        }, f, indent=2)


if __name__ == '__main__':
    run()