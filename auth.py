from flask import Blueprint, redirect, request, current_app, jsonify
from flask_login import logout_user, login_required

auth_bp = Blueprint('auth', __name__)


def get_frontend_url():
    """Generate the frontend URL based on configuration"""
    scheme = current_app.config.get('PREFERRED_URL_SCHEME', 'https')
    base_domain = current_app.config.get('BASE_DOMAIN', 'localhost')
    spawner_subdomain = current_app.config.get('SPAWNER_SUBDOMAIN', 'coder')

    if base_domain == 'localhost':
        # Local development - frontend runs on port 3000
        return 'http://localhost:3000'
    else:
        return f"{scheme}://{spawner_subdomain}.{base_domain}"


@auth_bp.route('/login', methods=['GET'])
def login():
    """Redirect to frontend login"""
    return redirect(f"{get_frontend_url()}/login")


@auth_bp.route('/signup', methods=['GET'])
def signup():
    """Redirect to frontend signup"""
    return redirect(f"{get_frontend_url()}/signup")


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout (for session-based auth)"""
    logout_user()
    return redirect(f"{get_frontend_url()}/login")
