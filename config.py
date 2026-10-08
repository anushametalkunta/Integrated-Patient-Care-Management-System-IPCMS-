import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration for the Integrated Patient Care Management System."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    # Prefer MySQL when DATABASE_URL is provided (see .env.example).
    # Falls back to a local SQLite file so the app runs out-of-the-box with zero setup.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True
