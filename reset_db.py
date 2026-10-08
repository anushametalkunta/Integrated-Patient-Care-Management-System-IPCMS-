"""Reset database — run once after schema upgrade: python reset_db.py"""
import os
from app import create_app
from extensions import db

app = create_app()
db_path = os.path.join(app.root_path, 'instance', 'app.db')

with app.app_context():
    db.drop_all()
    db.create_all()
    print('Database reset complete. Run: python seed_data.py')

if os.path.exists(db_path):
    print(f'Database file: {db_path}')
