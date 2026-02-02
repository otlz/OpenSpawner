"""
Admin-API Blueprint
Alle Endpoints erfordern Admin-Rechte.
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import db, User, UserState, AdminTakeoverSession, MagicLinkToken, UserContainer
from decorators import admin_required
from container_manager import ContainerManager
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

    current_app.logger.info(f"User {user.email} wurde von Admin {admin_id} gesperrt")

    return jsonify({
        'message': f'User {user.email} wurde gesperrt',
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
    current_app.logger.info(f"User {user.email} wurde von Admin {admin_id} entsperrt")

    return jsonify({
        'message': f'User {user.email} wurde entsperrt',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<int:user_id>/resend-verification', methods=['POST'])
@jwt_required()
@admin_required()
def resend_user_verification(user_id):
    """Sendet Magic Link erneut an einen Benutzer (für Admin-Funktion)"""
    from email_service import generate_magic_link_token, send_magic_link_email
    from models import MagicLinkToken

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    # Generiere neuen Magic Link Token
    token = generate_magic_link_token()
    expires_at = datetime.utcnow() + timedelta(seconds=Config.MAGIC_LINK_TOKEN_EXPIRY)

    magic_token = MagicLinkToken(
        user_id=user.id,
        token=token,
        token_type='login',
        expires_at=expires_at,
        ip_address=request.remote_addr
    )
    db.session.add(magic_token)
    db.session.commit()

    # Email senden
    email_sent = send_magic_link_email(user.email, token, 'login')

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Magic Link für User {user.email} wurde von Admin {admin_id} erneut gesendet")

    return jsonify({
        'message': f'Login-Link an {user.email} gesendet',
        'email_sent': email_sent
    }), 200


@admin_bp.route('/users/<int:user_id>/container', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user_container(user_id):
    """Loescht alle Container eines Benutzers (Multi-Container Support)"""
    admin_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if not user.containers:
        return jsonify({'error': 'User hat keine Container'}), 400

    container_mgr = ContainerManager()
    deleted_count = 0
    failed_containers = []

    # Iteriere über alle Container des Users
    for container in user.containers:
        if not container.container_id:
            continue

        try:
            container_mgr.stop_container(container.container_id)
            container_mgr.remove_container(container.container_id)
            deleted_count += 1
            current_app.logger.info(f"Container {container.container_id[:12]} (Type: {container.container_type}) gelöscht")

            # Lösche DB-Eintrag
            db.session.delete(container)
        except Exception as e:
            current_app.logger.warning(f"Container {container.container_id[:12]} konnte nicht gelöscht werden: {str(e)}")
            failed_containers.append(container.container_id[:12])

    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} löschte {deleted_count} Container von User {user.email}")

    if failed_containers:
        return jsonify({
            'message': f'{deleted_count} Container gelöscht, {len(failed_containers)} fehlgeschlagen',
            'failed': failed_containers,
            'deleted': deleted_count
        }), 207  # Multi-Status

    return jsonify({
        'message': f'Alle {deleted_count} Container von {user.email} wurden gelöscht',
        'deleted': deleted_count
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(user_id):
    """Loescht einen Benutzer komplett (DSGVO-konform)"""
    admin_id = get_jwt_identity()

    if int(admin_id) == user_id:
        return jsonify({'error': 'Du kannst dich nicht selbst loeschen'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    if user.is_admin:
        return jsonify({'error': 'Admins koennen nicht geloescht werden'}), 400

    email = user.email
    deletion_summary = {
        'containers_deleted': 0,
        'containers_failed': [],
        'magic_tokens_deleted': 0,
        'takeover_sessions_deleted': 0
    }

    # 1. Alle Docker-Container loeschen
    container_mgr = ContainerManager()
    for container in user.containers:
        if container.container_id:
            try:
                container_mgr.stop_container(container.container_id)
                container_mgr.remove_container(container.container_id)
                deletion_summary['containers_deleted'] += 1
                current_app.logger.info(f"Container {container.container_id[:12]} (Type: {container.container_type}) geloescht")
            except Exception as e:
                current_app.logger.warning(f"Container {container.container_id[:12]} fehlgeschlagen: {str(e)}")
                deletion_summary['containers_failed'].append(container.container_id[:12])

    # 2. MagicLinkToken loeschen (DSGVO: IP-Adressen)
    magic_tokens = MagicLinkToken.query.filter_by(user_id=user.id).all()
    for token in magic_tokens:
        db.session.delete(token)
        deletion_summary['magic_tokens_deleted'] += 1

    # 3. AdminTakeoverSession loeschen (als Target-User)
    takeover_sessions = AdminTakeoverSession.query.filter_by(target_user_id=user.id).all()
    for session in takeover_sessions:
        db.session.delete(session)
        deletion_summary['takeover_sessions_deleted'] += 1

    # 4. User loeschen (CASCADE loescht UserContainer-DB-Eintraege)
    db.session.delete(user)
    db.session.commit()

    # Logging
    current_app.logger.info(
        f"User {email} vollstaendig geloescht von Admin {admin_id}. "
        f"Summary: {deletion_summary}"
    )

    return jsonify({
        'message': f'User {email} wurde vollstaendig geloescht',
        'summary': deletion_summary
    }), 200


# ============================================================
# Takeover-Endpoints (Phase 2 - Dummy-Implementierung)
# ============================================================

@admin_bp.route('/users/<int:user_id>/takeover', methods=['POST'])
@jwt_required()
@admin_required()
def start_takeover(user_id):
    """
    Startet eine Takeover-Session für einen User-Container.
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

    current_app.logger.info(f"Admin {admin_id} hat Takeover für User {user.email} gestartet (Session {session.id})")

    return jsonify({
        'message': 'Takeover-Funktion ist noch nicht vollstaendig implementiert (Phase 2)',
        'session_id': session.id,
        'status': 'dummy',
        'note': 'Diese Funktion wird in einer späteren Version verfügbar sein'
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
            'admin_email': session.admin.email if session.admin else None,
            'target_user_id': session.target_user_id,
            'target_email': session.target_user.email if session.target_user else None,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'reason': session.reason
        })

    return jsonify({
        'sessions': sessions_list,
        'total': len(sessions_list)
    }), 200


@admin_bp.route('/debug', methods=['GET', 'POST'])
def debug_management():
    """
    Debug-Management Endpoint für Logs und Datenbank-Bereinigung
    ---
    tags:
      - Debug
    parameters:
      - name: action
        in: query
        type: string
        required: true
        enum:
          - view-logs
          - clear-logs
          - list-users
          - delete-email
          - delete-token
          - info
        description: Welche Aktion soll ausgeführt werden?
      - name: email
        in: query
        type: string
        required: false
        description: Email-Adresse des Users (erforderlich für delete-email und delete-token)
      - name: X-Debug-Token
        in: header
        type: string
        required: false
        description: Debug-Token alternativ zu JWT-Authentication
    security:
      - jwt: []
      - debug_token: []
    responses:
      200:
        description: Erfolgreich ausgeführt
        schema:
          type: object
          properties:
            action:
              type: string
              description: Die ausgeführte Aktion
            message:
              type: string
              description: Rückmeldung
            logs:
              type: string
              description: Log-Inhalte (nur bei view-logs)
            users:
              type: array
              description: Liste der User (nur bei list-users)
            tokens_deleted:
              type: integer
              description: Anzahl gelöschter Tokens
      400:
        description: Ungültige Parameter
        schema:
          type: object
          properties:
            error:
              type: string
      403:
        description: Authentifizierung erforderlich
      404:
        description: User oder Ressource nicht gefunden
    """
    # Authentifizierung prüfen
    debug_token = current_app.config.get('DEBUG_TOKEN')
    provided_token = request.headers.get('X-Debug-Token')

    # Versuch JWT-Auth
    is_admin = False
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            is_admin = user and user.is_admin
    except:
        pass

    # Authentifizierung validieren
    if not (is_admin or (debug_token and provided_token == debug_token)):
        return jsonify({'error': 'Authentifizierung erforderlich (JWT oder X-Debug-Token Header)'}), 403

    action = request.args.get('action', '').lower()

    # ===== view-logs =====
    if action == 'view-logs':
        log_file = current_app.config.get('LOG_FILE', '/app/logs/spawner.log')
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_100 = lines[-100:] if len(lines) > 100 else lines
            return jsonify({
                'action': 'view-logs',
                'source': 'Flask Log File',
                'total_lines': len(lines),
                'displayed_lines': len(last_100),
                'logs': ''.join(last_100)
            }), 200
        except FileNotFoundError:
            return jsonify({'error': f'Log-Datei nicht gefunden: {log_file}'}), 404
        except Exception as e:
            return jsonify({'error': f'Fehler beim Lesen der Logs: {str(e)}'}), 500

    # ===== clear-logs =====
    elif action == 'clear-logs':
        log_file = current_app.config.get('LOG_FILE', '/app/logs/spawner.log')
        try:
            with open(log_file, 'w') as f:
                f.write('')
            current_app.logger.info('[DEBUG] Logs wurden gelöscht')
            return jsonify({
                'action': 'clear-logs',
                'message': 'Log-Datei wurde geleert',
                'log_file': log_file
            }), 200
        except Exception as e:
            return jsonify({'error': f'Fehler beim Löschen der Logs: {str(e)}'}), 500

    # ===== delete-email =====
    elif action == 'delete-email':
        email = request.args.get('email', '').strip()
        if not email:
            return jsonify({'error': 'Parameter erforderlich: email'}), 400

        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'error': f'User {email} nicht gefunden'}), 404

            user_id = user.id
            email_deleted = user.email

            # Container löschen falls vorhanden
            if user.container_id:
                try:
                    container_mgr = ContainerManager()
                    container_mgr.stop_container(user.container_id)
                    container_mgr.remove_container(user.container_id)
                except:
                    pass

            # User und alle zugehörigen Daten löschen
            db.session.delete(user)
            db.session.commit()

            current_app.logger.info(f'[DEBUG] User {email_deleted} wurde gelöscht')

            return jsonify({
                'action': 'delete-email',
                'message': f'User {email_deleted} wurde gelöscht',
                'user_id': user_id
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Fehler beim Löschen: {str(e)}'}), 500

    # ===== delete-token =====
    elif action == 'delete-token':
        email = request.args.get('email', '').strip()
        if not email:
            return jsonify({'error': 'Parameter erforderlich: email'}), 400

        try:
            from models import MagicLinkToken
            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify({'error': f'User {email} nicht gefunden'}), 404

            tokens = MagicLinkToken.query.filter_by(user_id=user.id).all()
            count = len(tokens)

            for token in tokens:
                db.session.delete(token)
            db.session.commit()

            current_app.logger.info(f'[DEBUG] {count} Magic Link Tokens für {email} wurden gelöscht')

            return jsonify({
                'action': 'delete-token',
                'message': f'{count} Tokens für {email} gelöscht',
                'tokens_deleted': count
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Fehler: {str(e)}'}), 500

    # ===== list-users =====
    elif action == 'list-users':
        users = User.query.all()
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'email': user.email,
                'slug': user.slug,
                'state': user.state,
                'is_admin': user.is_admin,
                'is_blocked': user.is_blocked,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_used': user.last_used.isoformat() if user.last_used else None
            })

        return jsonify({
            'action': 'list-users',
            'users': users_list,
            'total': len(users_list)
        }), 200

    # ===== info =====
    elif action == 'info' or not action:
        return jsonify({
            'endpoint': '/api/admin/debug',
            'auth': 'X-Debug-Token Header oder Admin JWT',
            'actions': {
                'view-logs': 'Zeigt letzte 100 Zeilen der Logs',
                'clear-logs': 'Löscht alle Logs',
                'list-users': 'Listet alle registrierten User auf',
                'delete-email': 'Löscht User (Parameter: email=...)',
                'delete-token': 'Löscht Magic Link Tokens (Parameter: email=...)',
                'info': 'Diese Hilfe'
            },
            'examples': [
                'GET /api/admin/debug?action=view-logs -H "X-Debug-Token: xxx"',
                'GET /api/admin/debug?action=list-users -H "X-Debug-Token: xxx"',
                'GET /api/admin/debug?action=delete-email&email=test@example.com',
                'GET /api/admin/debug?action=delete-token&email=test@example.com'
            ]
        }), 200

    else:
        return jsonify({'error': f'Unbekannte Action: {action}'}), 400
