import json
import os

from flask import Blueprint, render_template
from flask_login import login_required
from decorators import roles_required

testing_qa_bp = Blueprint('testing_qa', __name__, url_prefix='/testing-qa')

RESULTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qa_results.json')


@testing_qa_bp.route('/')
@login_required
@roles_required('Admin')
def index():
    data = None
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            data = json.load(f)

    return render_template('testing_qa.html', data=data, active_page='testing_qa')