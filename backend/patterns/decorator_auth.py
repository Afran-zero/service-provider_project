from flask import redirect, url_for
from flask_login import current_user, LoginManager
from functools import wraps

login_manager = LoginManager()

def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_view