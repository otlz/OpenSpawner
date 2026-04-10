"""Auth-Weiterleitungen zum Frontend."""
from flask import Blueprint, redirect, current_app
from flask_login import logout_user, login_required

auth_bp = Blueprint('auth', __name__)


def get_frontend_url():
    """Erstellt die Frontend-URL basierend auf der Konfiguration."""
    scheme = current_app.config.get('PREFERRED_URL_SCHEME', 'https')
    base_domain = current_app.config.get('BASE_DOMAIN', 'localhost')
    spawner_subdomain = current_app.config.get('SPAWNER_SUBDOMAIN', 'coder')

    if base_domain == 'localhost':
        return 'http://localhost:3000'
    else:
        return f"{scheme}://{spawner_subdomain}.{base_domain}"


@auth_bp.route('/login', methods=['GET'])
def login():
    """Weiterleitung zur Frontend-Loginseite."""
    return redirect(f"{get_frontend_url()}/login")


@auth_bp.route('/signup', methods=['GET'])
def signup():
    """Weiterleitung zur Frontend-Registrierungsseite."""
    return redirect(f"{get_frontend_url()}/signup")


@auth_bp.route('/logout')
@login_required
def logout():
    """Session-basierter Logout mit Weiterleitung."""
    logout_user()
    return redirect(f"{get_frontend_url()}/login")
