from flask import Blueprint, jsonify, request, current_app, redirect, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta, datetime
from models import db, User, UserState, MagicLinkToken, UserContainer
from container_manager import ContainerManager
from email_service import (
    generate_slug_from_email,
    generate_magic_link_token,
    send_magic_link_email,
    check_rate_limit
)
from config import Config
import re

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _get_service_url(slug_or_path, container_port=None):
    """Generate service URL based on mode (Traefik vs local port mapping)"""
    if Config.TRAEFIK_ENABLED:
        scheme = Config.PREFERRED_URL_SCHEME
        domain = f"{Config.SPAWNER_SUBDOMAIN}.{Config.BASE_DOMAIN}"
        return f"{scheme}://{domain}/{slug_or_path}"
    else:
        if container_port and container_port != 8080:
            return f"http://localhost:{container_port}"
        return None

# Token blacklist for logout
token_blacklist = set()


def create_auth_response(access_token, user_data, expires_in):
    """Create a JSON response with JWT token as HttpOnly cookie"""
    response_data = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': expires_in,
        'user': user_data
    }

    response = make_response(jsonify(response_data))

    # Set JWT as HttpOnly cookie
    # HttpOnly prevents JavaScript access
    # Secure: only via HTTPS
    # SameSite: CSRF protection
    # Domain: available for all subpaths and subdomains
    response.set_cookie(
        'spawner_token',
        access_token,
        max_age=expires_in,
        httponly=True,
        secure=True,  # Only via HTTPS
        samesite='Lax',  # CSRF protection
        path='/',  # Available for all paths
        domain=f".{Config.BASE_DOMAIN}"  # Available for all subpaths and subdomains
    )

    return response


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API login with magic link (passwordless)"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Email is required'}), 400

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
    """API signup with magic link (passwordless)"""
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

    # Check if this is the first user -> becomes admin
    is_first_user = User.query.count() == 0

    user = User(email=email, slug=slug)
    user.state = UserState.REGISTERED.value
    user.is_admin = is_first_user
    db.session.add(user)
    db.session.flush()  # So that user.id is available

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
    """Verify signup magic link and create JWT"""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 400

    # Find token in database
    magic_token = MagicLinkToken.query.filter_by(
        token=token,
        token_type='signup'
    ).first()

    if not magic_token:
        return jsonify({'error': 'Invalid or expired link'}), 400

    # Check validity
    if not magic_token.is_valid():
        return jsonify({'error': 'This link has expired or has already been used'}), 400

    # Get user
    user = magic_token.user

    # Set user status to VERIFIED
    user.state = UserState.VERIFIED.value
    magic_token.mark_as_used()
    db.session.commit()

    # Spawn container (only on first signup) - multi-container compatible
    if not user.container_id:
        try:
            container_mgr = ContainerManager()
            # Use spawn_multi_container with default template (template-01)
            default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
            container_id, port = container_mgr.spawn_multi_container(
                user.id,
                user.slug,
                default_template
            )
            # Save in primary container (backwards compatibility)
            if user.containers:
                user.containers[0].container_id = container_id
                user.containers[0].container_port = port
            db.session.commit()
            current_app.logger.info(f"[SPAWNER] Container {default_template} created for user {user.id} (slug: {user.slug})")
        except Exception as e:
            current_app.logger.error(f"Container spawn failed: {str(e)}")
            # Note: container spawn is optional during signup
            # User is still created, container can be created manually later

    # Create JWT
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'is_admin': user.is_admin}
    )

    current_app.logger.info(f"[SIGNUP] User {user.email} successfully registered")

    user_data = {
        'id': user.id,
        'email': user.email,
        'slug': user.slug,
        'is_admin': user.is_admin,
        'state': user.state,
        'container_id': user.container_id
    }

    return create_auth_response(access_token, user_data, int(expires.total_seconds())), 200


@api_bp.route('/auth/verify-login', methods=['GET'])
def api_verify_login():
    """Verify login magic link and create JWT"""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 400

    # Find token
    magic_token = MagicLinkToken.query.filter_by(
        token=token,
        token_type='login'
    ).first()

    if not magic_token:
        return jsonify({'error': 'Invalid or expired link'}), 400

    # Check validity
    if not magic_token.is_valid():
        return jsonify({'error': 'This link has expired or has already been used'}), 400

    # Get user
    user = magic_token.user

    # Check if user is blocked
    if user.is_blocked:
        return jsonify({'error': 'Your account has been suspended'}), 403

    # Check if email is verified
    if user.state == UserState.REGISTERED.value:
        return jsonify({'error': 'Please verify your email address first'}), 403

    # Mark token as used
    magic_token.mark_as_used()

    # Container management - start or recreate
    container_mgr = ContainerManager()

    if user.container_id:
        try:
            status = container_mgr.get_container_status(user.container_id)
            if status != 'running':
                # Restart container
                container_mgr.start_container(user.container_id)
                current_app.logger.info(f"[LOGIN] Container {user.container_id[:12]} restarted for user {user.email}")
        except Exception as e:
            # Container no longer exists - create new one
            current_app.logger.warning(f"Container {user.container_id[:12]} not found, creating new one: {str(e)}")
            try:
                # Use spawn_multi_container for primary container
                default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
                container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
                if user.containers:
                    user.containers[0].container_id = container_id
                    user.containers[0].container_port = port
                current_app.logger.info(f"[LOGIN] New container {default_template} created for user {user.email} (slug: {user.slug})")
            except Exception as spawn_error:
                current_app.logger.error(f"Container spawn failed: {str(spawn_error)}")
    else:
        # No container exists - create new one
        try:
            # Use spawn_multi_container for primary container
            default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
            container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
            if user.containers:
                user.containers[0].container_id = container_id
                user.containers[0].container_port = port
            current_app.logger.info(f"[LOGIN] Container created for user {user.email} (slug: {user.slug})")
        except Exception as e:
            current_app.logger.error(f"Container spawn failed: {str(e)}")

    user.last_used = datetime.utcnow()
    db.session.commit()

    # Create JWT
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'is_admin': user.is_admin}
    )

    current_app.logger.info(f"[LOGIN] User {user.email} successfully logged in")

    user_data = {
        'id': user.id,
        'email': user.email,
        'slug': user.slug,
        'is_admin': user.is_admin,
        'state': user.state,
        'container_id': user.container_id
    }

    return create_auth_response(access_token, user_data, int(expires.total_seconds())), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """API logout - invalidate token and delete cookie"""
    jti = get_jwt()['jti']
    token_blacklist.add(jti)

    # Create response and delete cookie
    response = make_response(jsonify({'message': 'Successfully logged out'}))
    response.delete_cookie('spawner_token', path='/')

    return response, 200


@api_bp.route('/user/me', methods=['GET'])
@jwt_required()
def api_user_me():
    """Return current user and container info"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

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
    """Return container status"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

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
    """Restart container"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    container_mgr = ContainerManager()

    # Stop old container if it exists
    if user.container_id:
        try:
            container_mgr.stop_container(user.container_id)
            container_mgr.remove_container(user.container_id)
        except Exception as e:
            current_app.logger.warning(f"Old container could not be stopped: {str(e)}")

    # Start new container - multi-container compatible
    try:
        # Use spawn_multi_container for primary container
        default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
        container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
        if user.containers:
            user.containers[0].container_id = container_id
            user.containers[0].container_port = port

        # Set state to ACTIVE on container start (if still VERIFIED)
        if user.state == UserState.VERIFIED.value:
            user.state = UserState.ACTIVE.value

        # Update last_used
        user.last_used = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Container successfully restarted',
            'container_id': container_id,
            'status': 'running'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Container restart failed: {str(e)}")
        return jsonify({'error': f'Container restart failed: {str(e)}'}), 500


def check_if_token_revoked(jwt_header, jwt_payload):
    """Callback for flask-jwt-extended to check revoked tokens"""
    jti = jwt_payload['jti']
    return jti in token_blacklist


# ============================================================
# Multi-Container Support Endpoints
# ============================================================

@api_bp.route('/user/containers', methods=['GET'])
@jwt_required()
def api_user_containers():
    """Return all containers for the user"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Build container list
    containers = []
    for container_type, template in current_app.config['CONTAINER_TEMPLATES'].items():
        # Find existing container
        user_container = UserContainer.query.filter_by(
            user_id=user.id,
            container_type=container_type
        ).first()

        # Service URL
        container_port = user_container.container_port if user_container else None
        slug_with_suffix = f"{user.slug}-{container_type}"
        service_url = _get_service_url(slug_with_suffix, container_port)

        # Determine status
        status = 'not_created'
        if user_container and user_container.container_id:
            try:
                container_mgr = ContainerManager()
                status = container_mgr.get_container_status(user_container.container_id)
            except Exception:
                status = 'error'

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
            'blocked_at': user_container.blocked_at.isoformat() if user_container and user_container.blocked_at else None
        })

    return jsonify({'containers': containers}), 200


@api_bp.route('/container/launch/<container_type>', methods=['POST'])
@jwt_required()
def api_container_launch(container_type):
    """Create container on-demand and return service URL"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if type is valid
    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Invalid container type: {container_type}'}), 400

    # Check if container already exists
    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    # Launch protection: blocked containers must not be started (Phase 7)
    if user_container and user_container.is_blocked:
        return jsonify({
            'error': 'This container has been blocked by an administrator',
            'blocked_at': user_container.blocked_at.isoformat() if user_container.blocked_at else None
        }), 403

    container_mgr = ContainerManager()

    if user_container and user_container.container_id:
        # Container exists - check status
        try:
            status = container_mgr.get_container_status(user_container.container_id)
            if status == 'not_found':
                # Container not found - recreate
                raise Exception(f"Container {user_container.container_id[:12]} no longer exists")

            if status != 'running':
                # Restart container
                start_result = container_mgr.start_container(user_container.container_id)
                if not start_result:
                    # Start failed - recreate
                    raise Exception(f"Container {user_container.container_id[:12]} could not be started")
                current_app.logger.info(f"[MULTI-CONTAINER] Container {user_container.container_id[:12]} restarted")

            # Update last_used
            user_container.last_used = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            # Container no longer exists or could not be started - recreate
            current_app.logger.warning(f"Container {user_container.container_id[:12]} unavailable, creating new one: {str(e)}")
            try:
                template = current_app.config['CONTAINER_TEMPLATES'][container_type]
                container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, container_type)
                user_container.container_id = container_id
                user_container.container_port = port
                user_container.last_used = datetime.utcnow()
                db.session.commit()
                current_app.logger.info(f"[MULTI-CONTAINER] New {container_type} container created for {user.email}")
            except Exception as spawn_error:
                current_app.logger.error(f"Container spawn failed: {str(spawn_error)}")
                return jsonify({'error': 'Container could not be created'}), 500
    else:
        # Container does not exist yet - create new one
        try:
            template = current_app.config['CONTAINER_TEMPLATES'][container_type]
            container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, container_type)

            user_container = UserContainer(
                user_id=user.id,
                container_type=container_type,
                container_id=container_id,
                container_port=port,
                template_image=template['image'],
                last_used=datetime.utcnow()
            )
            db.session.add(user_container)
            db.session.commit()

            current_app.logger.info(f"[MULTI-CONTAINER] {container_type} container created for {user.email}")
        except Exception as e:
            current_app.logger.error(f"Container spawn failed: {str(e)}")
            return jsonify({'error': f'Container could not be created: {str(e)}'}), 500

    # Generate service URL
    slug_with_suffix = f"{user.slug}-{container_type}"
    service_url = _get_service_url(slug_with_suffix, user_container.container_port)

    return jsonify({
        'message': 'Container ready',
        'service_url': service_url,
        'container_id': user_container.container_id,
        'status': 'running'
    }), 200
