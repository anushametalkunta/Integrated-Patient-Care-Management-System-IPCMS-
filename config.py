import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    if os.environ.get('VERCEL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'sqlite:////tmp/app.db'
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
