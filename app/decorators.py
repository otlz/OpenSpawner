"""
Dekoratoren für Zugriffskontrolle.
Müssen immer NACH @jwt_required() verwendet werden.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models import User


def admin_required():
    """Prüft ob der Benutzer Admin-Rechte hat. Muss nach @jwt_required() stehen."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User not found'}), 404

            if not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


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
