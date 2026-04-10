"""
Admin-API-Blueprint.
Alle Endpunkte erfordern Admin-Rechte (außer /debug mit Debug-Token).
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.models import db, User, UserState, UserRole, AdminTakeoverSession, MagicLinkToken, UserContainer, EmailRule
from app.decorators import admin_required
from app.services.container_manager import ContainerManager
from app.services.container_orchestrator import ContainerOrchestrator
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    """Listet alle Benutzer mit Container-Informationen auf."""
    users = User.query.all()

    users_list = []
    for user in users:
        user_dict = user.to_dict()
        # Add container info (Phase 7)
        user_dict['container_count'] = len(user.containers)
        user_dict['containers'] = [c.to_dict() for c in user.containers]
        users_list.append(user_dict)

    return jsonify({
        'users': users_list,
        'total': len(users_list)
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required()
def get_user(user_id):
    """Gibt Details eines einzelnen Benutzers zurück."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Retrieve container status
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
    """Sperrt einen Benutzer und alle seine Container (kaskadierend)."""
    admin_id = get_jwt_identity()

    if int(admin_id) == user_id:
        return jsonify({'error': 'Cannot block yourself'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_admin:
        return jsonify({'error': 'Admins cannot be blocked'}), 400

    if user.is_blocked:
        return jsonify({'error': 'User is already blocked'}), 400

    user.is_blocked = True
    user.blocked_at = datetime.utcnow()
    user.blocked_by = int(admin_id)

    # CASCADE: Block all user containers (Phase 7)
    container_mgr = ContainerManager()
    blocked_containers = 0

    for container in user.containers:
        if not container.is_blocked:
            try:
                if container.container_id:
                    container_mgr.stop_container(container.container_id)
                    container.status = 'stopped'
            except Exception as e:
                current_app.logger.warning(f"Failed to stop container: {str(e)}")

            container.is_blocked = True
            container.blocked_at = datetime.utcnow()
            container.blocked_by = int(admin_id)
            blocked_containers += 1

    db.session.commit()

    current_app.logger.info(f"User {user.email} blocked by admin {admin_id} (cascade: {blocked_containers} containers blocked)")

    return jsonify({
        'message': f'User {user.email} blocked',
        'user': user.to_dict(),
        'containers_blocked': blocked_containers
    }), 200


@admin_bp.route('/users/<int:user_id>/unblock', methods=['POST'])
@jwt_required()
@admin_required()
def unblock_user(user_id):
    """Entsperrt einen Benutzer (Container-Sperren bleiben bestehen)."""
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.is_blocked:
        return jsonify({'error': 'User is not blocked'}), 400

    user.is_blocked = False
    user.blocked_at = None
    user.blocked_by = None
    db.session.commit()

    admin_id = get_jwt_identity()
    current_app.logger.info(f"User {user.email} unblocked by admin {admin_id}")

    # Note: Container-level blocks are NOT automatically lifted
    # They must be unblocked separately via /api/admin/containers/<id>/unblock
    unblocked_containers = 0
    for container in user.containers:
        if container.is_blocked:
            unblocked_containers += 1

    return jsonify({
        'message': f'User {user.email} unblocked',
        'user': user.to_dict(),
        'note': f'{unblocked_containers} containers are still blocked and must be unblocked separately'
    }), 200


@admin_bp.route('/users/<int:user_id>/resend-verification', methods=['POST'])
@jwt_required()
@admin_required()
def resend_user_verification(user_id):
    """Sendet einen Magic-Link erneut an einen Benutzer (Admin-Funktion)."""
    from app.services.email_service import generate_magic_link_token, send_magic_link_email

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Generate new magic link token
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

    # Send email
    email_sent = send_magic_link_email(user.email, token, 'login')

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Magic link for user {user.email} resent by admin {admin_id}")

    return jsonify({
        'message': f'Login link sent to {user.email}',
        'email_sent': email_sent
    }), 200


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required()
def change_user_role(user_id):
    """Ändert die Rolle eines Benutzers. Admin kann eigene Rolle nicht ändern."""
    admin_id = int(get_jwt_identity())

    if admin_id == user_id:
        return jsonify({'error': 'Cannot change your own role'}), 400

    data = request.get_json()
    new_role = data.get('role', '').lower()

    valid_roles = [r.value for r in UserRole]
    if new_role not in valid_roles:
        return jsonify({'error': f'Invalid role. Must be: {", ".join(valid_roles)}'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    old_role = user.role
    user.role = new_role
    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} changed role of {user.email}: {old_role} -> {new_role}")

    return jsonify({
        'message': f'Rolle für {user.email} geändert: {new_role}',
        'user': user.to_dict()
    }), 200


# ============================================================
# Email Rules (Whitelist/Blacklist)
# ============================================================

@admin_bp.route('/email-rules', methods=['GET'])
@jwt_required()
@admin_required()
def get_email_rules():
    """Listet alle E-Mail-Whitelist/Blacklist-Regeln auf."""
    rules = EmailRule.query.order_by(EmailRule.created_at.desc()).all()
    return jsonify({
        'rules': [r.to_dict() for r in rules],
        'total': len(rules)
    }), 200


@admin_bp.route('/email-rules', methods=['POST'])
@jwt_required()
@admin_required()
def create_email_rule():
    """Erstellt eine neue Whitelist- oder Blacklist-Regel."""
    admin_id = int(get_jwt_identity())
    data = request.get_json()

    pattern = data.get('pattern', '').strip().lower()
    rule_type = data.get('rule_type', '').lower()

    if not pattern:
        return jsonify({'error': 'Pattern is required'}), 400
    if rule_type not in ('whitelist', 'blacklist'):
        return jsonify({'error': 'rule_type must be whitelist or blacklist'}), 400

    existing = EmailRule.query.filter_by(pattern=pattern, rule_type=rule_type).first()
    if existing:
        return jsonify({'error': f'Regel existiert bereits: {pattern} ({rule_type})'}), 409

    rule = EmailRule(
        pattern=pattern,
        rule_type=rule_type,
        created_by=admin_id
    )
    db.session.add(rule)
    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} created email rule: {rule_type} {pattern}")

    return jsonify({
        'message': f'{rule_type}-Regel erstellt: {pattern}',
        'rule': rule.to_dict()
    }), 201


@admin_bp.route('/email-rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_email_rule(rule_id):
    """Löscht eine E-Mail-Regel."""
    admin_id = int(get_jwt_identity())

    rule = EmailRule.query.get(rule_id)
    if not rule:
        return jsonify({'error': 'Rule not found'}), 404

    pattern = rule.pattern
    rule_type = rule.rule_type
    db.session.delete(rule)
    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} deleted email rule: {rule_type} {pattern}")

    return jsonify({
        'message': f'{rule_type}-Regel gelöscht: {pattern}'
    }), 200


@admin_bp.route('/users/<int:user_id>/container', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user_container(user_id):
    """Löscht bestimmte Container eines Benutzers (Multi-Container)."""
    admin_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.containers:
        return jsonify({
            'message': 'User has no containers',
            'deleted': 0,
            'failed': [],
            'skipped': True
        }), 200

    # Get container_ids from request body if provided
    data = request.get_json() or {}
    container_ids = data.get('container_ids', [])

    # Determine which containers to delete
    containers_to_delete = user.containers
    if container_ids:
        # Only delete specified containers
        containers_to_delete = [c for c in user.containers if c.id in container_ids]

    if not containers_to_delete:
        return jsonify({
            'message': 'No containers found to delete',
            'deleted': 0,
            'failed': [],
            'skipped': True
        }), 200

    container_mgr = ContainerManager()
    deleted_count = 0
    failed_containers = []

    # Iterate over containers to be deleted
    for container in containers_to_delete:
        if not container.container_id:
            continue

        try:
            container_mgr.stop_container(container.container_id)
            container_mgr.remove_container(container.container_id)
            deleted_count += 1
            current_app.logger.info(f"Container {container.container_id[:12]} (type: {container.container_type}) deleted")

            # Delete DB entry
            db.session.delete(container)
        except Exception as e:
            current_app.logger.warning(f"Container {container.container_id[:12]} could not be deleted: {str(e)}")
            failed_containers.append(container.container_id[:12])

    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} deleted {deleted_count} containers of user {user.email}")

    return jsonify({
        'message': f'{deleted_count} containers deleted' +
                   (f', {len(failed_containers)} failed' if failed_containers else ''),
        'deleted': deleted_count,
        'failed': failed_containers,
        'partial_failure': len(failed_containers) > 0
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(user_id):
    """Löscht einen Benutzer vollständig (DSGVO-konform)."""
    admin_id = get_jwt_identity()

    if int(admin_id) == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_admin:
        return jsonify({'error': 'Admins cannot be deleted'}), 400

    email = user.email
    deletion_summary = {
        'containers_deleted': 0,
        'containers_failed': [],
        'magic_tokens_deleted': 0,
        'takeover_sessions_deleted': 0
    }

    # 1. Delete all Docker containers and their volumes
    # Use manager directly (not orchestrator.destroy) because cascade='all, delete-orphan'
    # on User.containers handles DB deletion when user is deleted below
    container_mgr = ContainerManager()
    for container in user.containers:
        if container.container_id:
            try:
                container_mgr.stop_container(container.container_id)
                container_mgr.remove_container(container.container_id)
                deletion_summary['containers_deleted'] += 1
                current_app.logger.info(f"Container {container.container_id[:12]} (type: {container.container_type}) deleted")
            except Exception as e:
                current_app.logger.warning(f"Container {container.container_id[:12]} failed: {str(e)}")
                deletion_summary['containers_failed'].append(container.container_id[:12])
        # Clean up named volumes
        template = Config.CONTAINER_TEMPLATES.get(container.container_type, {})
        container_mgr.remove_volumes(container.user_id, container.container_type, template.get('volumes', []))

    # 2. Delete MagicLinkTokens (GDPR: IP addresses)
    magic_tokens = MagicLinkToken.query.filter_by(user_id=user.id).all()
    for token in magic_tokens:
        db.session.delete(token)
        deletion_summary['magic_tokens_deleted'] += 1

    # 3. Delete AdminTakeoverSessions (as target user)
    takeover_sessions = AdminTakeoverSession.query.filter_by(target_user_id=user.id).all()
    for session in takeover_sessions:
        db.session.delete(session)
        deletion_summary['takeover_sessions_deleted'] += 1

    # 4. Delete user (CASCADE deletes UserContainer DB entries)
    db.session.delete(user)
    db.session.commit()

    # Logging
    current_app.logger.info(
        f"User {email} completely deleted by admin {admin_id}. "
        f"Summary: {deletion_summary}"
    )

    return jsonify({
        'message': f'User {email} completely deleted',
        'summary': deletion_summary
    }), 200


# ============================================================
# Takeover Endpoints (Phase 2 - Dummy Implementation)
# ============================================================

@admin_bp.route('/users/<int:user_id>/takeover', methods=['POST'])
@jwt_required()
@admin_required()
def start_takeover(user_id):
    """Startet eine Takeover-Session für einen Benutzer-Container (Dummy)."""
    admin_id = get_jwt_identity()
    data = request.get_json() or {}
    reason = data.get('reason', '')

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.container_id:
        return jsonify({'error': 'User has no container'}), 400

    # Create takeover session (logging only)
    session = AdminTakeoverSession(
        admin_id=int(admin_id),
        target_user_id=user_id,
        reason=reason
    )
    db.session.add(session)
    db.session.commit()

    current_app.logger.info(f"Admin {admin_id} started takeover for user {user.email} (session {session.id})")

    return jsonify({
        'message': 'Takeover feature is not yet fully implemented (Phase 2)',
        'session_id': session.id,
        'status': 'dummy',
        'note': 'This feature will be available in a later version'
    }), 200


@admin_bp.route('/takeover/<int:session_id>/end', methods=['POST'])
@jwt_required()
@admin_required()
def end_takeover(session_id):
    """Beendet eine Takeover-Session (Dummy)."""
    session = AdminTakeoverSession.query.get(session_id)

    if not session:
        return jsonify({'error': 'Takeover session not found'}), 404

    if session.ended_at:
        return jsonify({'error': 'Takeover session has already ended'}), 400

    session.ended_at = datetime.utcnow()
    db.session.commit()

    admin_id = get_jwt_identity()
    current_app.logger.info(f"Admin {admin_id} ended takeover session {session_id}")

    return jsonify({
        'message': 'Takeover session ended',
        'session_id': session_id
    }), 200


@admin_bp.route('/takeover/active', methods=['GET'])
@jwt_required()
@admin_required()
def get_active_takeovers():
    """Listet alle aktiven Takeover-Sessions auf."""
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


def _check_debug_auth():
    """Prüft Authentifizierung für Debug-Endpunkt (JWT oder Debug-Token)."""
    debug_token = current_app.config.get('DEBUG_TOKEN')
    provided_token = request.headers.get('X-Debug-Token')

    # JWT-Auth versuchen
    is_admin = False
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            is_admin = user and user.is_admin
    except Exception:
        pass

    return is_admin or (debug_token and provided_token == debug_token)


def _debug_view_logs():
    """Zeigt die letzten 100 Zeilen der Log-Datei."""
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
        return jsonify({'error': f'Log file not found: {log_file}'}), 404
    except Exception as e:
        return jsonify({'error': f'Error reading logs: {str(e)}'}), 500


def _debug_clear_logs():
    """Leert die Log-Datei."""
    log_file = current_app.config.get('LOG_FILE', '/app/logs/spawner.log')
    try:
        with open(log_file, 'w') as f:
            f.write('')
        current_app.logger.info('[DEBUG] Logs cleared')
        return jsonify({
            'action': 'clear-logs',
            'message': 'Log file cleared',
            'log_file': log_file
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error clearing logs: {str(e)}'}), 500


def _debug_delete_email():
    """Löscht einen Benutzer anhand der E-Mail-Adresse (inkl. Container)."""
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Required parameter: email'}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': f'User {email} not found'}), 404

        user_id = user.id
        email_deleted = user.email

        # Container löschen falls vorhanden
        if user.container_id:
            try:
                container_mgr = ContainerManager()
                container_mgr.stop_container(user.container_id)
                container_mgr.remove_container(user.container_id)
            except Exception:
                pass

        db.session.delete(user)
        db.session.commit()

        current_app.logger.info(f'[DEBUG] User {email_deleted} deleted')

        return jsonify({
            'action': 'delete-email',
            'message': f'User {email_deleted} deleted',
            'user_id': user_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting: {str(e)}'}), 500


def _debug_delete_token():
    """Löscht alle Magic-Link-Tokens eines Benutzers."""
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({'error': 'Required parameter: email'}), 400

    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': f'User {email} not found'}), 404

        tokens = MagicLinkToken.query.filter_by(user_id=user.id).all()
        count = len(tokens)

        for token in tokens:
            db.session.delete(token)
        db.session.commit()

        current_app.logger.info(f'[DEBUG] {count} magic link tokens for {email} deleted')

        return jsonify({
            'action': 'delete-token',
            'message': f'{count} tokens for {email} deleted',
            'tokens_deleted': count
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error: {str(e)}'}), 500


def _debug_list_users():
    """Listet alle registrierten Benutzer auf."""
    users = User.query.all()
    users_list = [{
        'id': user.id,
        'email': user.email,
        'slug': user.slug,
        'state': user.state,
        'is_admin': user.is_admin,
        'is_blocked': user.is_blocked,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_used': user.last_used.isoformat() if user.last_used else None
    } for user in users]

    return jsonify({
        'action': 'list-users',
        'users': users_list,
        'total': len(users_list)
    }), 200


def _debug_info():
    """Gibt Hilfe-Informationen zum Debug-Endpunkt zurück."""
    return jsonify({
        'endpoint': '/api/admin/debug',
        'auth': 'X-Debug-Token header or admin JWT',
        'actions': {
            'view-logs': 'Show last 100 lines of logs',
            'clear-logs': 'Clear all logs',
            'list-users': 'List all registered users',
            'delete-email': 'Delete user (parameter: email=...)',
            'delete-token': 'Delete magic link tokens (parameter: email=...)',
            'info': 'This help'
        },
        'examples': [
            'GET /api/admin/debug?action=view-logs -H "X-Debug-Token: xxx"',
            'GET /api/admin/debug?action=list-users -H "X-Debug-Token: xxx"',
            'GET /api/admin/debug?action=delete-email&email=test@example.com',
            'GET /api/admin/debug?action=delete-token&email=test@example.com'
        ]
    }), 200


# Dispatch-Tabelle für Debug-Actions
_DEBUG_HANDLERS = {
    'view-logs': _debug_view_logs,
    'clear-logs': _debug_clear_logs,
    'delete-email': _debug_delete_email,
    'delete-token': _debug_delete_token,
    'list-users': _debug_list_users,
    'info': _debug_info,
}


@admin_bp.route('/debug', methods=['GET', 'POST'])
def debug_management():
    """Debug-Endpunkt für Logs und Datenbankbereinigung (Dispatch-Pattern)."""
    if not _check_debug_auth():
        return jsonify({'error': 'Authentication required (JWT or X-Debug-Token header)'}), 403

    action = request.args.get('action', '').lower()

    # Kein Action angegeben → Info anzeigen
    if not action:
        return _debug_info()

    handler = _DEBUG_HANDLERS.get(action)
    if not handler:
        return jsonify({'error': f'Unknown action: {action}'}), 400

    return handler()


# ============================================================
# Container Blocking Endpoints (Phase 7)
# ============================================================

@admin_bp.route('/containers/<int:container_id>/block', methods=['POST'])
@jwt_required()
@admin_required()
def block_container(container_id):
    """Sperrt einen einzelnen Benutzer-Container."""
    admin_id = get_jwt_identity()

    container = UserContainer.query.get(container_id)
    if not container:
        return jsonify({'error': 'Container not found'}), 404

    if container.is_blocked:
        return jsonify({'error': 'Container is already blocked'}), 400

    # Stop container
    container_mgr = ContainerManager()
    try:
        if container.container_id:
            container_mgr.stop_container(container.container_id)
            container.status = 'stopped'
    except Exception as e:
        current_app.logger.warning(f"Failed to stop container: {str(e)}")

    # Update DB
    container.is_blocked = True
    container.blocked_at = datetime.utcnow()
    container.blocked_by = int(admin_id)
    db.session.commit()

    current_app.logger.info(f"Container {container.id} ({container.container_type}) blocked by admin {admin_id}")

    return jsonify({
        'message': f'Container {container.container_type} blocked'
    }), 200


@admin_bp.route('/containers/<int:container_id>/unblock', methods=['POST'])
@jwt_required()
@admin_required()
def unblock_container(container_id):
    """Entsperrt einen einzelnen Benutzer-Container."""
    admin_id = get_jwt_identity()

    container = UserContainer.query.get(container_id)
    if not container:
        return jsonify({'error': 'Container not found'}), 404

    if not container.is_blocked:
        return jsonify({'error': 'Container is not blocked'}), 400

    # Update DB
    container.is_blocked = False
    container.blocked_at = None
    container.blocked_by = None
    db.session.commit()

    current_app.logger.info(f"Container {container.id} ({container.container_type}) unblocked by admin {admin_id}")

    return jsonify({
        'message': f'Container {container.container_type} unblocked',
        'info': 'User can now start the container manually'
    }), 200


@admin_bp.route('/containers/bulk-block', methods=['POST'])
@jwt_required()
@admin_required()
def bulk_block_containers():
    """Sperrt mehrere Container gleichzeitig."""
    admin_id = get_jwt_identity()
    container_ids = request.json.get('container_ids', [])

    if not container_ids:
        return jsonify({'error': 'container_ids array required'}), 400

    success = 0
    failed = []
    container_mgr = ContainerManager()

    for container_id in container_ids:
        container = UserContainer.query.get(container_id)
        if not container or container.is_blocked:
            failed.append(container_id)
            continue

        try:
            if container.container_id:
                container_mgr.stop_container(container.container_id)
                container.status = 'stopped'
        except Exception as e:
            current_app.logger.warning(f"Failed to stop container {container_id}: {str(e)}")

        container.is_blocked = True
        container.blocked_at = datetime.utcnow()
        container.blocked_by = int(admin_id)
        success += 1

    db.session.commit()

    return jsonify({
        'message': f'{success} containers blocked',
        'failed': failed
    }), 200 if not failed else 207


@admin_bp.route('/containers/bulk-unblock', methods=['POST'])
@jwt_required()
@admin_required()
def bulk_unblock_containers():
    """Entsperrt mehrere Container gleichzeitig."""
    admin_id = get_jwt_identity()
    container_ids = request.json.get('container_ids', [])

    if not container_ids:
        return jsonify({'error': 'container_ids array required'}), 400

    success = 0
    failed = []

    for container_id in container_ids:
        container = UserContainer.query.get(container_id)
        if not container or not container.is_blocked:
            failed.append(container_id)
            continue

        container.is_blocked = False
        container.blocked_at = None
        container.blocked_by = None
        success += 1

    db.session.commit()

    return jsonify({
        'message': f'{success} containers unblocked',
        'failed': failed
    }), 200 if not failed else 207


@admin_bp.route('/config/reload', methods=['POST'])
@jwt_required()
@admin_required()
def reload_config():
    """Lädt .env neu und aktualisiert alle Konfigurationswerte (ohne Neustart)."""
    try:
        from dotenv import load_dotenv
        import os

        admin_id = get_jwt_identity()

        current_app.logger.info(f"[CONFIG] Admin {admin_id} requesting config reload")

        # Reload .env
        load_dotenv()

        # Update all important config values (without needing to reload the Config class)
        # These values are used directly in the endpoints
        old_smtp_user = current_app.config.get('SMTP_USER')
        old_smtp_from = current_app.config.get('SMTP_FROM')
        old_base_domain = current_app.config.get('BASE_DOMAIN')

        # Read new values
        new_smtp_user = os.getenv('SMTP_USER')
        new_smtp_from = os.getenv('SMTP_FROM')
        new_base_domain = os.getenv('BASE_DOMAIN')

        # Update Flask config
        current_app.config['SMTP_USER'] = new_smtp_user
        current_app.config['SMTP_FROM'] = new_smtp_from
        current_app.config['BASE_DOMAIN'] = new_base_domain
        current_app.config['SMTP_HOST'] = os.getenv('SMTP_HOST')
        current_app.config['SMTP_PORT'] = os.getenv('SMTP_PORT')
        current_app.config['SMTP_PASSWORD'] = os.getenv('SMTP_PASSWORD')

        changes = []
        if old_smtp_user != new_smtp_user:
            changes.append(f"SMTP_USER: {old_smtp_user} → {new_smtp_user}")
        if old_smtp_from != new_smtp_from:
            changes.append(f"SMTP_FROM: {old_smtp_from} → {new_smtp_from}")
        if old_base_domain != new_base_domain:
            changes.append(f"BASE_DOMAIN: {old_base_domain} → {new_base_domain}")

        current_app.logger.info(f"[CONFIG] Reload successful. Changes: {', '.join(changes) if changes else 'none'}")

        return jsonify({
            'message': 'Config successfully reloaded',
            'timestamp': datetime.utcnow().isoformat(),
            'changes': changes if changes else ['no changes detected']
        }), 200

    except Exception as e:
        current_app.logger.error(f"[CONFIG] Reload failed: {str(e)}")
        return jsonify({'error': f'Config reload failed: {str(e)}'}), 500
