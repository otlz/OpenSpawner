"""
Decorators fuer Zugriffskontrollen
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User


def admin_required():
    """
    Decorator der Admin-Rechte prueft.
    Muss NACH @jwt_required() verwendet werden.

    Usage:
        @api_bp.route('/admin/users')
        @jwt_required()
        @admin_required()
        def get_users():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User nicht gefunden'}), 404

            if not user.is_admin:
                return jsonify({'error': 'Admin-Rechte erforderlich'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def verified_required():
    """
    Decorator der prueft ob Email verifiziert ist.
    Muss NACH @jwt_required() verwendet werden.

    Usage:
        @api_bp.route('/container/action')
        @jwt_required()
        @verified_required()
        def container_action():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from models import UserState

            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))

            if not user:
                return jsonify({'error': 'User nicht gefunden'}), 404

            if user.state == UserState.REGISTERED.value:
                return jsonify({
                    'error': 'Email nicht verifiziert',
                    'needs_verification': True
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
