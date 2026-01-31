"""
Admin-API Blueprint
Alle Endpoints erfordern Admin-Rechte.
"""
import secrets
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, User, UserState, AdminTakeoverSession
from decorators import admin_required
from container_manager import ContainerManager
from email_service import (
    generate_verification_token,
    send_verification_email,
    send_password_reset_email
)
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    """Listet alle Benutzer auf"""
    users = User.query.all()

    users_list = []
    for user in users:
        users_list.append(user.to_dict())

    return jsonify({
        'users': users_list,
        'total': len(users_list)
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required()
def get_user(user_id):
    """Gibt Details eines einzelnen Users zurueck"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    # Container-Status abrufen
    container_status = 'no_container'
    if user.container_id:
        try:
            container_mgr = ContainerManager()
            container_status = container_mgr.get_container_status(user.container_id)
        except Exception:
            container_status = 'error'

    user_data = user.to_dict()
    user_data['container_status'] = container_status

    return jsonify({'user': user_data}), 200


@admin_bp.route('/users/<int:user_id>/block', methods=['POST'])
@jwt_required()
@admin_required()
def block_user(user_id):
    """Sperrt einen Benutzer"""
    admin_id = get_jwt_identity()

    if int(admin_id) == user_id:
        return jsonify({'error': 'Du kannst dich nicht selbst sperren'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if user.is_admin:
        return jsonify({'error': 'Admins koennen nicht gesperrt werden'}), 400

    if user.is_blocked:
        return jsonify({'error': 'User ist bereits gesperrt'}), 400

    user.is_blocked = True
    user.blocked_at = datetime.utcnow()
    user.blocked_by = int(admin_id)
    db.session.commit()

    current_app.logger.info(f"User {user.username} wurde von Admin {admin_id} gesperrt")

    return jsonify({
        'message': f'User {user.username} wurde gesperrt',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
@jwt_required()
@admin_required()
def unblock_user(user_id):
    """Entsperrt einen Benutzer"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if not user.is_blocked:
        return jsonify({'error': 'User ist nicht gesperrt'}), 400

    user.is_blocked = False
    user.blocked_at = None
    user.blocked_by = None
    db.session.commit()

    admin_id = get_jwt_identity()
    current_app.logger.info(f"User {user.username} wurde von Admin {admin_id} entsperrt")

    return jsonify({
        'message': f'User {user.username} wurde entsperrt',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@jwt_required()
@admin_required()
def reset_user_password(user_id):
    """Setzt das Passwort eines Benutzers zurueck"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    data = request.get_json() or {}

    # Neues Passwort: entweder angegeben oder zufaellig generiert
    new_password = data.get('password')
    if not new_password:
        new_password = secrets.token_urlsafe(12)

    if len(new_password) < 6:
        return jsonify({'error': 'Passwort muss mindestens 6 Zeichen lang sein'}), 400

    user.set_password(new_password)
    db.session.commit()

    # Email mit neuem Passwort senden
    email_sent = send_password_reset_email(user.email, user.username, new_password)

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Passwort von User {user.username} wurde von Admin {admin_id} zurueckgesetzt")

    return jsonify({
        'message': f'Passwort von {user.username} wurde zurueckgesetzt',
        'email_sent': email_sent,
        'password_generated': 'password' not in (data or {})
    }), 200


@admin_bp.route('/users/<int:user_id>/resend-verification', methods=['POST'])
@jwt_required()
@admin_required()
def resend_user_verification(user_id):
    """Sendet Verifizierungs-Email erneut an einen Benutzer"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if user.state != UserState.REGISTERED.value:
        return jsonify({'error': 'User ist bereits verifiziert'}), 400

    # Neuen Token generieren
    user.verification_token = generate_verification_token()
    user.verification_sent_at = datetime.utcnow()
    db.session.commit()

    # Email senden
    frontend_url = Config.FRONTEND_URL
    email_sent = send_verification_email(
        user.email,
        user.username,
        user.verification_token,
        frontend_url
    )

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Verifizierungs-Email fuer User {user.username} wurde von Admin {admin_id} erneut gesendet")

    return jsonify({
        'message': f'Verifizierungs-Email an {user.email} gesendet',
        'email_sent': email_sent
    }), 200


@admin_bp.route('/users/<int:user_id>/container', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user_container(user_id):
    """Loescht den Container eines Benutzers"""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if not user.container_id:
        return jsonify({'error': 'User hat keinen Container'}), 400

    container_mgr = ContainerManager()

    try:
        container_mgr.stop_container(user.container_id)
        container_mgr.remove_container(user.container_id)
    except Exception as e:
        current_app.logger.warning(f"Fehler beim Loeschen des Containers: {str(e)}")

    old_container_id = user.container_id
    user.container_id = None
    user.container_port = None
    db.session.commit()

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Container {old_container_id[:12]} von User {user.username} wurde von Admin {admin_id} geloescht")

    return jsonify({
        'message': f'Container von {user.username} wurde geloescht',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(user_id):
    """Loescht einen Benutzer komplett"""
    admin_id = get_jwt_identity()

    if int(admin_id) == user_id:
        return jsonify({'error': 'Du kannst dich nicht selbst loeschen'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if user.is_admin:
        return jsonify({'error': 'Admins koennen nicht geloescht werden'}), 400

    # Container loeschen falls vorhanden
    if user.container_id:
        container_mgr = ContainerManager()
        try:
            container_mgr.stop_container(user.container_id)
            container_mgr.remove_container(user.container_id)
        except Exception as e:
            current_app.logger.warning(f"Fehler beim Loeschen des Containers: {str(e)}")

    username = user.username
    db.session.delete(user)
    db.session.commit()

    current_app.logger.info(f"User {username} wurde von Admin {admin_id} geloescht")

    return jsonify({
        'message': f'User {username} wurde geloescht'
    }), 200


# ============================================================
# Takeover-Endpoints (Phase 2 - Dummy-Implementierung)
# ============================================================

@admin_bp.route('/users/<int:user_id>/takeover', methods=['POST'])
@jwt_required()
@admin_required()
def start_takeover(user_id):
    """
    Startet eine Takeover-Session fuer einen User-Container.
    DUMMY-IMPLEMENTIERUNG - wird in Phase 2 vollstaendig implementiert.
    """
    admin_id = get_jwt_identity()
    data = request.get_json() or {}
    reason = data.get('reason', '')

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if not user.container_id:
        return jsonify({'error': 'User hat keinen Container'}), 400

    # Takeover-Session erstellen (nur Protokollierung)
    session = AdminTakeoverSession(
        admin_id=int(admin_id),
        target_user_id=user_id,
        reason=reason
    )
    db.session.add(session)
    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} hat Takeover fuer User {user.username} gestartet (Session {session.id})")

    return jsonify({
        'message': 'Takeover-Funktion ist noch nicht vollstaendig implementiert (Phase 2)',
        'session_id': session.id,
        'status': 'dummy',
        'note': 'Diese Funktion wird in einer spaeteren Version verfuegbar sein'
    }), 200


@admin_bp.route('/takeover/<int:session_id>/end', methods=['POST'])
@jwt_required()
@admin_required()
def end_takeover(session_id):
    """
    Beendet eine Takeover-Session.
    DUMMY-IMPLEMENTIERUNG - wird in Phase 2 vollstaendig implementiert.
    """
    session = AdminTakeoverSession.query.get(session_id)

    if not session:
        return jsonify({'error': 'Takeover-Session nicht gefunden'}), 404

    if session.ended_at:
        return jsonify({'error': 'Takeover-Session ist bereits beendet'}), 400

    session.ended_at = datetime.utcnow()
    db.session.commit()

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Admin {admin_id} hat Takeover-Session {session_id} beendet")

    return jsonify({
        'message': 'Takeover-Session beendet',
        'session_id': session_id
    }), 200


@admin_bp.route('/takeover/active', methods=['GET'])
@jwt_required()
@admin_required()
def get_active_takeovers():
    """Listet alle aktiven Takeover-Sessions auf"""
    sessions = AdminTakeoverSession.query.filter_by(ended_at=None).all()

    sessions_list = []
    for session in sessions:
        sessions_list.append({
            'id': session.id,
            'admin_id': session.admin_id,
            'admin_username': session.admin.username if session.admin else None,
            'target_user_id': session.target_user_id,
            'target_username': session.target_user.username if session.target_user else None,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'reason': session.reason
        })

    return jsonify({
        'sessions': sessions_list,
        'total': len(sessions_list)
    }), 200
