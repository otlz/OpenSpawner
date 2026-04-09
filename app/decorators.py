"""
Decorators for access control
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User


def admin_required():
    """
    Decorator that checks for admin privileges.
    Must be used AFTER @jwt_required().

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
                return jsonify({'error': 'User not found'}), 404

            if not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def verified_required():
    """
    Decorator that checks if email is verified.
    Must be used AFTER @jwt_required().

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
            from app.models import UserState

            verify_jwt_in_request()
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
