"""
Dekoratoren für Zugriffskontrolle.
Müssen immer NACH @jwt_required() verwendet werden.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User

# Rollen-Hierarchie: admin > manager > user
ROLE_HIERARCHY = {'admin': 3, 'manager': 2, 'user': 1}


def role_required(minimum_role):
    """Prüft ob der Benutzer mindestens die angegebene Rolle hat. Muss nach @jwt_required() stehen."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User not found'}), 404

            user_level = ROLE_HIERARCHY.get(user.role, 0)
            required_level = ROLE_HIERARCHY.get(minimum_role, 999)

            if user_level < required_level:
                return jsonify({'error': f'{minimum_role.title()} privileges required'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required():
    """Prüft ob der Benutzer Admin-Rechte hat. Alias für role_required('admin')."""
    return role_required('admin')


def manager_required():
    """Prüft ob der Benutzer mindestens Manager-Rechte hat. Alias für role_required('manager')."""
    return role_required('manager')


def verified_required():
    """Prüft ob die E-Mail-Adresse verifiziert ist. Muss nach @jwt_required() stehen."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from app.models import UserState

            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User not found'}), 404

            if user.state == UserState.REGISTERED.value:
                return jsonify({
                    'error': 'Email not verified',
                    'needs_verification': True
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
