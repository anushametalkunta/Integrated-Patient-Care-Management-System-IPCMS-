from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Restrict a route to only the given roles, e.g. @roles_required('Admin', 'Nurse')."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                if current_user.is_authenticated:
                    from routes.api import log_audit
                    log_audit(
                        current_user.id,
                        'unauthorized_access',
                        f'{current_user.role} tried to access a page restricted to: {", ".join(roles)}'
                    )
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator