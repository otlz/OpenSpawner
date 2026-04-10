"""
API-Blueprint für Authentifizierung, Benutzer- und Container-Verwaltung.
"""
from flask import Blueprint, jsonify, request, current_app, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta, datetime
from app.models import db, User, UserState, UserRole, MagicLinkToken, UserContainer
from app.services.container_manager import ContainerManager
from app.services.container_orchestrator import ContainerOrchestrator
from app.services.email_service import (
    generate_slug_from_email,
    generate_magic_link_token,
    send_magic_link_email,
    check_rate_limit,
    check_email_allowed
)
from config import Config
import re

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Token-Blacklist für Logout (In-Memory, reicht für Single-Instance)
token_blacklist = set()


# ============================================================
# Hilfsfunktionen
# ============================================================

def _get_current_user():
    """Gets the current authenticated user from JWT identity. Returns (user, error_response)."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return None, (jsonify({'error': 'User not found'}), 404)
    return user, None


def _get_service_url(slug_or_path, container_port=None):
    """Erstellt die Service-URL je nach Modus (Traefik vs. lokaler Port)."""
    if Config.TRAEFIK_ENABLED:
        scheme = Config.PREFERRED_URL_SCHEME
        domain = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"
        return f"{scheme}://{domain}/{slug_or_path}"
    else:
        if container_port and container_port != 8080:
            return f"http://localhost:{container_port}"
        return None


def _get_default_template():
    """Gibt den ersten Template-Typ aus der Konfiguration zurück."""
    return list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]


def _ensure_user_has_container(user):
    """
    Stellt sicher, dass der Benutzer einen laufenden Primär-Container hat.
    Erstellt oder startet den Container bei Bedarf neu.
    Gibt (container_id, port) zurück oder (None, None) bei Fehler.
    """
    default_template = _get_default_template()
    try:
        orchestrator = ContainerOrchestrator()
        uc, _ = orchestrator.ensure_running(user, default_template)
        return uc.container_id, uc.container_port
    except Exception as e:
        current_app.logger.error(f"Container spawn failed: {str(e)}")
        return None, None


def _create_jwt_response(user):
    """Erstellt JWT-Token und Auth-Response mit HttpOnly-Cookie für den Benutzer."""
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'is_admin': user.is_admin, 'role': user.role}
    )

    user_data = {
        'id': user.id,
        'email': user.email,
        'slug': user.slug,
        'role': user.role,
        'is_admin': user.is_admin,
        'state': user.state,
        'container_id': user.container_id
    }

    return _create_auth_response(access_token, user_data, int(expires.total_seconds()))


def _create_auth_response(access_token, user_data, expires_in):
    """Erstellt eine JSON-Response mit JWT als HttpOnly-Cookie."""
    response_data = {
        'expires_in': expires_in,
        'user': user_data
    }

    response = make_response(jsonify(response_data))

    # HttpOnly: no JS access, Secure: HTTPS only (except localhost), SameSite: CSRF protection
    is_localhost = Config.BASE_DOMAIN == 'localhost'
    response.set_cookie(
        'spawner_token',
        access_token,
        max_age=expires_in,
        httponly=True,
        secure=not is_localhost,
        samesite='Strict',
        path='/',
        domain=None if is_localhost else f".{Config.BASE_DOMAIN}"
    )

    return response


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Login per Magic-Link (passwortlos). Sendet E-Mail mit Login-Link."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Check email whitelist/blacklist
    allowed, reason = check_email_allowed(email)
    if not allowed:
        return jsonify({'error': reason}), 403

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        # Security: Same message as success (prevents user enumeration)
        return jsonify({
            'message': 'If this email is registered, a login link has been sent.'
        }), 200

    # Check if user is blocked
    if user.is_blocked:
        return jsonify({'error': 'Your account has been suspended'}), 403

    # Rate limiting
    if not check_rate_limit(email):
        return jsonify({'error': 'Too many requests. Please try again later.'}), 429

    # Generate magic link token
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
    try:
        send_magic_link_email(email, token, 'login')
    except Exception as e:
        current_app.logger.error(f"Email sending failed: {str(e)}")
        return jsonify({'error': 'Email could not be sent'}), 500

    current_app.logger.info(f"[LOGIN] Magic link sent to {email}")

    return jsonify({
        'message': 'A login link has been sent to your email. Please check your inbox.'
    }), 200


@api_bp.route('/auth/signup', methods=['POST'])
def api_signup():
    """Registrierung per Magic-Link. Erstellt Benutzer und sendet Verifizierungs-Link."""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()

    # Validation
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    # Check email format (simple regex)
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Invalid email address'}), 400

    # Check email whitelist/blacklist
    allowed, reason = check_email_allowed(email)
    if not allowed:
        return jsonify({'error': reason}), 403

    # Check if email is already registered
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        # Instead of error: send login link (better UX, prevents user enumeration)
        if existing_user.is_blocked:
            return jsonify({'error': 'Your account has been suspended'}), 403

        # Check rate limit
        if not check_rate_limit(email):
            return jsonify({'error': 'Too many requests. Please try again later.'}), 429

        # Generate magic link token for login
        token = generate_magic_link_token()
        expires_at = datetime.utcnow() + timedelta(seconds=Config.MAGIC_LINK_TOKEN_EXPIRY)

        magic_token = MagicLinkToken(
            user_id=existing_user.id,
            token=token,
            token_type='login',
            expires_at=expires_at,
            ip_address=request.remote_addr
        )
        db.session.add(magic_token)
        db.session.commit()

        # Send email
        try:
            send_magic_link_email(email, token, 'login')
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            return jsonify({'error': 'Email could not be sent'}), 500

        current_app.logger.info(f"[SIGNUP] Email {email} already exists - login link sent")

        # Same message as for new registration (prevents user enumeration)
        return jsonify({
            'message': 'A signup link has been sent to your email. Please check your inbox.'
        }), 200

    # Rate limiting
    if not check_rate_limit(email):
        return jsonify({'error': 'Too many requests. Please try again later.'}), 429

    # Create user (initial status=REGISTERED)
    slug = generate_slug_from_email(email)

    # Check if slug already exists (unlikely but possible)
    slug_exists = User.query.filter_by(slug=slug).first()
    if slug_exists:
        # Add random suffix
        slug = slug + generate_magic_link_token()[:4]

    user = User(email=email, slug=slug)
    user.state = UserState.REGISTERED.value
    user.role = UserRole.USER.value  # Default to user
    db.session.add(user)
    db.session.flush()  # So that user.id is available

    # First user becomes admin (check after flush to reduce race window)
    if User.query.count() == 1:
        user.role = UserRole.ADMIN.value

    # Generate magic link token
    token = generate_magic_link_token()
    expires_at = datetime.utcnow() + timedelta(seconds=Config.MAGIC_LINK_TOKEN_EXPIRY)

    magic_token = MagicLinkToken(
        user_id=user.id,
        token=token,
        token_type='signup',
        expires_at=expires_at,
        ip_address=request.remote_addr
    )
    db.session.add(magic_token)
    db.session.commit()

    # Send email
    try:
        send_magic_link_email(email, token, 'signup')
    except Exception as e:
        current_app.logger.error(f"Email sending failed: {str(e)}")
        # Cleanup: delete user and token
        db.session.delete(magic_token)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'error': 'Email could not be sent'}), 500

    current_app.logger.info(f"[SIGNUP] Magic link sent to {email}")

    return jsonify({
        'message': 'A signup link has been sent to your email. Please check your inbox.'
    }), 200


@api_bp.route('/auth/verify-signup', methods=['GET'])
def api_verify_signup():
    """Verifiziert den Signup-Magic-Link und erstellt JWT."""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 400

    magic_token = MagicLinkToken.query.filter_by(token=token, token_type='signup').first()

    if not magic_token:
        return jsonify({'error': 'Invalid or expired link'}), 400

    if not magic_token.is_valid():
        return jsonify({'error': 'This link has expired or has already been used'}), 400

    user = magic_token.user

    # Status auf VERIFIED setzen und Token entwerten
    user.state = UserState.VERIFIED.value
    magic_token.mark_as_used()
    db.session.commit()

    # Container erstellen (nur beim ersten Signup, optional)
    if not user.container_id:
        _ensure_user_has_container(user)
        db.session.commit()

    current_app.logger.info(f"[SIGNUP] User {user.email} successfully registered")

    return _create_jwt_response(user), 200


@api_bp.route('/auth/verify-login', methods=['GET'])
def api_verify_login():
    """Verifiziert den Login-Magic-Link und erstellt JWT."""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 400

    magic_token = MagicLinkToken.query.filter_by(token=token, token_type='login').first()

    if not magic_token:
        return jsonify({'error': 'Invalid or expired link'}), 400

    if not magic_token.is_valid():
        return jsonify({'error': 'This link has expired or has already been used'}), 400

    user = magic_token.user

    if user.is_blocked:
        return jsonify({'error': 'Your account has been suspended'}), 403

    if user.state == UserState.REGISTERED.value:
        return jsonify({'error': 'Please verify your email address first'}), 403

    magic_token.mark_as_used()

    # Container sicherstellen (starten oder neu erstellen)
    _ensure_user_has_container(user)

    user.last_used = datetime.utcnow()
    db.session.commit()

    current_app.logger.info(f"[LOGIN] User {user.email} successfully logged in")

    return _create_jwt_response(user), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """Logout — Token invalidieren, Container stoppen und Cookie löschen."""
    user_id = get_jwt_identity()
    jti = get_jwt()['jti']
    token_blacklist.add(jti)

    # Stop all running containers for this user (best-effort)
    try:
        user = User.query.get(int(user_id))
        if user:
            orchestrator = ContainerOrchestrator()
            stopped = orchestrator.stop_all_for_user(user)
            if stopped:
                current_app.logger.info(f"[LOGOUT] Stopped {stopped} containers for {user.email}")
    except Exception as e:
        current_app.logger.warning(f"[LOGOUT] Failed to stop containers: {str(e)}")

    # Create response and delete cookie
    is_localhost = Config.BASE_DOMAIN == 'localhost'
    response = make_response(jsonify({'message': 'Successfully logged out'}))
    response.delete_cookie(
        'spawner_token',
        path='/',
        domain=None if is_localhost else f".{Config.BASE_DOMAIN}",
        samesite='Strict',
        secure=not is_localhost,
    )

    return response, 200


@api_bp.route('/user/me', methods=['GET'])
@jwt_required()
def api_user_me():
    """Gibt aktuelle Benutzer- und Container-Informationen zurück."""
    user, err = _get_current_user()
    if err:
        return err

    # Calculate service URL
    service_url = _get_service_url(user.slug, user.container_port)

    # Get container status
    container_status = 'unknown'
    if user.container_id:
        try:
            container_mgr = ContainerManager()
            container_status = container_mgr.get_container_status(user.container_id)
        except Exception:
            container_status = 'error'

    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'slug': user.slug,
            'role': user.role,
            'is_admin': user.is_admin,
            'state': user.state,
            'last_used': user.last_used.isoformat() if user.last_used else None,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'container': {
            'id': user.container_id,
            'port': user.container_port,
            'status': container_status,
            'service_url': service_url
        }
    }), 200


@api_bp.route('/container/status', methods=['GET'])
@jwt_required()
def api_container_status():
    """Gibt den Container-Status des Benutzers zurück."""
    user, err = _get_current_user()
    if err:
        return err

    container_status = 'no_container'
    if user.container_id:
        try:
            container_mgr = ContainerManager()
            container_status = container_mgr.get_container_status(user.container_id)
        except Exception as e:
            container_status = f'error: {str(e)}'

    return jsonify({
        'container_id': user.container_id,
        'status': container_status
    }), 200


@api_bp.route('/container/restart', methods=['POST'])
@jwt_required()
def api_container_restart():
    """Startet den Primär-Container des Benutzers neu (stop + start, preserves data)."""
    user, err = _get_current_user()
    if err:
        return err

    orchestrator = ContainerOrchestrator()
    default_template = _get_default_template()

    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=default_template
    ).first()

    if user_container and user_container.container_id:
        # Try docker restart (stop + start, preserves state)
        if not orchestrator.restart(user_container):
            # Fallback: recreate
            orchestrator.recreate(user, user_container)
    else:
        # No container — create one
        uc, _ = orchestrator.ensure_running(user, default_template)
        user_container = uc

    # Status auf ACTIVE setzen (falls noch VERIFIED)
    if user.state == UserState.VERIFIED.value:
        user.state = UserState.ACTIVE.value

    user.last_used = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Container successfully restarted',
        'container_id': user_container.container_id,
        'status': 'running'
    }), 200


def check_if_token_revoked(jwt_header, jwt_payload):
    """Callback für flask-jwt-extended: Prüft ob ein Token widerrufen wurde."""
    jti = jwt_payload['jti']
    return jti in token_blacklist


# ============================================================
# Multi-Container Support Endpoints
# ============================================================

@api_bp.route('/user/containers', methods=['GET'])
@jwt_required()
def api_user_containers():
    """Gibt alle Container des Benutzers zurück (Multi-Container-Unterstützung)."""
    user, err = _get_current_user()
    if err:
        return err

    # Build container list (single query instead of N+1)
    all_user_containers = {
        uc.container_type: uc
        for uc in UserContainer.query.filter_by(user_id=user.id).all()
    }
    containers = []
    for container_type, template in current_app.config['CONTAINER_TEMPLATES'].items():
        user_container = all_user_containers.get(container_type)

        # Service URL
        container_port = user_container.container_port if user_container else None
        slug_with_suffix = f"{user.slug}-{container_type}"
        service_url = _get_service_url(slug_with_suffix, container_port)

        # Determine status (query Docker for ground truth, sync DB)
        status = 'not_created'
        if user_container and user_container.container_id:
            try:
                container_mgr = ContainerManager()
                status = container_mgr.get_container_status(user_container.container_id)
                # Sync DB status with Docker reality
                if status == 'not_found':
                    user_container.status = 'not_created'
                    user_container.container_id = None
                    status = 'not_created'
                elif user_container.status != status:
                    user_container.status = status
            except Exception:
                status = 'error'
        elif user_container:
            status = user_container.status or 'not_created'

        containers.append({
            'type': container_type,
            'display_name': template['display_name'],
            'description': template['description'],
            'status': status,
            'service_url': service_url,
            'container_id': user_container.container_id if user_container else None,
            'created_at': user_container.created_at.isoformat() if user_container and user_container.created_at else None,
            'last_used': user_container.last_used.isoformat() if user_container and user_container.last_used else None,
            # Phase 7: Container Blocking
            'is_blocked': user_container.is_blocked if user_container else False,
            'blocked_at': user_container.blocked_at.isoformat() if user_container and user_container.blocked_at else None,
            # Template metadata
            'os': template.get('os', 'Linux'),
            'software': template.get('software', ''),
            'icon': template.get('icon', ''),
            'port': template.get('port', 8080),
            'category': template.get('category', 'software'),
        })

    # Persist any status corrections from Docker queries
    db.session.commit()

    categories = current_app.config.get('TEMPLATE_CATEGORIES', [])
    return jsonify({'containers': containers, 'categories': categories}), 200


@api_bp.route('/container/launch/<container_type>', methods=['POST'])
@jwt_required()
def api_container_launch(container_type):
    """Erstellt oder startet einen Container on-demand (stop+start, kein recreate)."""
    user, err = _get_current_user()
    if err:
        return err

    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    # Launch protection: blocked containers must not be started
    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    if user_container and user_container.is_blocked:
        return jsonify({
            'error': 'This container has been blocked by an administrator',
            'blocked_at': user_container.blocked_at.isoformat() if user_container.blocked_at else None
        }), 403

    try:
        orchestrator = ContainerOrchestrator()
        uc, _ = orchestrator.ensure_running(user, container_type)
    except Exception as e:
        current_app.logger.error(f"Container launch failed: {str(e)}")
        return jsonify({'error': f'Container could not be created: {str(e)}'}), 500

    slug_with_suffix = f"{user.slug}-{container_type}"
    service_url = _get_service_url(slug_with_suffix, uc.container_port)

    return jsonify({
        'message': 'Container ready',
        'service_url': service_url,
        'container_id': uc.container_id,
        'status': 'running'
    }), 200


@api_bp.route('/container/stop/<container_type>', methods=['POST'])
@jwt_required()
def api_container_stop(container_type):
    """Stoppt einen laufenden Container des Benutzers (Daten bleiben erhalten)."""
    user, err = _get_current_user()
    if err:
        return err

    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    if not user_container or not user_container.container_id:
        return jsonify({'error': 'No container found'}), 404

    if user_container.is_blocked:
        return jsonify({'error': 'This container has been blocked by an administrator'}), 403

    try:
        orchestrator = ContainerOrchestrator()
        orchestrator.stop(user_container)
        current_app.logger.info(f"[SPAWNER] Container {user_container.container_id[:12]} stopped by user {user.email}")
        return jsonify({'message': 'Container stopped', 'status': 'stopped'}), 200
    except Exception as e:
        current_app.logger.error(f"Container stop failed: {str(e)}")
        return jsonify({'error': f'Failed to stop container: {str(e)}'}), 500


@api_bp.route('/container/<container_type>', methods=['DELETE'])
@jwt_required()
def api_container_delete(container_type):
    """Löscht einen Container des Benutzers (Container + DB-Eintrag, Volumes optional)."""
    user, err = _get_current_user()
    if err:
        return err

    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    if not user_container:
        return jsonify({'error': 'No container found'}), 404

    if user_container.is_blocked:
        return jsonify({'error': 'This container has been blocked by an administrator'}), 403

    try:
        delete_volumes = request.args.get('delete_volumes', 'false').lower() == 'true'
        orchestrator = ContainerOrchestrator()
        orchestrator.destroy(user_container, delete_volumes=delete_volumes)
        current_app.logger.info(f"[SPAWNER] Container {container_type} deleted by user {user.email}")
        return jsonify({'message': 'Container deleted'}), 200
    except Exception as e:
        current_app.logger.error(f"Container delete failed: {str(e)}")
        return jsonify({'error': f'Failed to delete container: {str(e)}'}), 500


@api_bp.route('/container/restart/<container_type>', methods=['POST'])
@jwt_required()
def api_container_restart_type(container_type):
    """Startet einen Container neu (docker restart, Daten bleiben erhalten)."""
    user, err = _get_current_user()
    if err:
        return err

    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    if user_container and user_container.is_blocked:
        return jsonify({'error': 'This container has been blocked by an administrator'}), 403

    orchestrator = ContainerOrchestrator()

    try:
        if user_container and user_container.container_id:
            # Try docker restart (preserves container state)
            if not orchestrator.restart(user_container):
                # Fallback: recreate from image
                orchestrator.recreate(user, user_container)
        else:
            # No container — create one
            uc, _ = orchestrator.ensure_running(user, container_type)
            user_container = uc

        current_app.logger.info(f"[SPAWNER] Container {container_type} restarted for user {user.email}")

        slug_with_suffix = f"{user.slug}-{container_type}"
        service_url = _get_service_url(slug_with_suffix, user_container.container_port)

        return jsonify({
            'message': 'Container restarted',
            'container_id': user_container.container_id,
            'service_url': service_url,
            'status': 'running'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Container restart failed: {str(e)}")
        return jsonify({'error': f'Failed to restart container: {str(e)}'}), 500


@api_bp.route('/container/recreate/<container_type>', methods=['POST'])
@jwt_required()
def api_container_recreate(container_type):
    """Erstellt einen Container komplett neu (destroy + create, für Image-Updates)."""
    user, err = _get_current_user()
    if err:
        return err

    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    if user_container and user_container.is_blocked:
        return jsonify({'error': 'This container has been blocked by an administrator'}), 403

    orchestrator = ContainerOrchestrator()

    try:
        if user_container and user_container.container_id:
            container_id, port = orchestrator.recreate(user, user_container)
        else:
            uc, _ = orchestrator.ensure_running(user, container_type)
            user_container = uc

        current_app.logger.info(f"[SPAWNER] Container {container_type} recreated for user {user.email}")

        slug_with_suffix = f"{user.slug}-{container_type}"
        service_url = _get_service_url(slug_with_suffix, user_container.container_port)

        return jsonify({
            'message': 'Container recreated',
            'container_id': user_container.container_id,
            'service_url': service_url,
            'status': 'running'
        }), 200
    except Exception as e:
        current_app.logger.error(f"Container recreate failed: {str(e)}")
        return jsonify({'error': f'Failed to recreate container: {str(e)}'}), 500


@api_bp.route('/container/heartbeat/<container_type>', methods=['POST'])
@jwt_required()
def api_container_heartbeat(container_type):
    """Frontend-Heartbeat: hält Container am Leben während aktiver Nutzung."""
    user_id = get_jwt_identity()

    user_container = UserContainer.query.filter_by(
        user_id=int(user_id),
        container_type=container_type
    ).first()

    if not user_container:
        return jsonify({'error': 'Container not found'}), 404

    user_container.last_used = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status': 'ok',
        'idle_timeout': Config.CONTAINER_IDLE_TIMEOUT
    }), 200
