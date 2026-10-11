import os
from flask import Flask, render_template

from config import Config
from extensions import db, login_manager
from models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not os.environ.get('VERCEL'):
       os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.patient import patient_bp
    from routes.doctor import doctor_bp
    from routes.appointment import appointment_bp
    from routes.ehr import ehr_bp
    from routes.consultation import consultation_bp
    from routes.prescription import prescription_bp
    from routes.laboratory import laboratory_bp
    from routes.medical_history import medical_history_bp
    from routes.reports import reports_bp
    from routes.pharmacy import pharmacy_bp
    from routes.billing import billing_bp
    from routes.api import api_bp
    from routes.users import users_bp
    from routes.notifications import notifications_bp 
    from routes.api_management import api_management_bp
    from routes.system_integration import system_integration_bp
    from routes.security_management import security_management_bp
    from routes.settings import settings_bp
    from routes.testing_qa import testing_qa_bp
    from routes.feedback import feedback_bp
    from routes.deployment_status import deployment_status_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(ehr_bp)
    app.register_blueprint(consultation_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(laboratory_bp)
    app.register_blueprint(medical_history_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_management_bp)
    app.register_blueprint(system_integration_bp)
    app.register_blueprint(security_management_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(testing_qa_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(deployment_status_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.before_request
    def start_timer():
        from flask import g
        import time
        g.start_time = time.time()

    @app.after_request
    def log_api_call(response):
        from flask import g, request
        import time
        if request.path.startswith('/api/') and hasattr(g, 'start_time'):
            from models import APICallLog
            duration_ms = int((time.time() - g.start_time) * 1000)
            try:
                log_entry = APICallLog(
                    endpoint=request.path,
                    method=request.method,
                    status_code=response.status_code,
                    response_time_ms=duration_ms
                )
                db.session.add(log_entry)
                db.session.commit()
            except Exception:
                db.session.rollback()
        return response

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
