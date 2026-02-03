from flask import Blueprint, jsonify, request, current_app, redirect
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

# Token-Blacklist für Logout
token_blacklist = set()


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API-Login mit Magic Link (Passwordless)"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten uebermittelt'}), 400

    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Email ist erforderlich'}), 400

    # Prüfe ob User existiert
    user = User.query.filter_by(email=email).first()
    if not user:
        # Security: Gleiche Nachricht wie bei Erfolg (verhindert User-Enumeration)
        return jsonify({
            'message': 'Falls diese Email registriert ist, wurde ein Login-Link gesendet.'
        }), 200

    # Prüfe ob User blockiert
    if user.is_blocked:
        return jsonify({'error': 'Dein Account wurde gesperrt'}), 403

    # Rate-Limiting
    if not check_rate_limit(email):
        return jsonify({'error': 'Zu viele Anfragen. Bitte versuche es später erneut.'}), 429

    # Generiere Magic Link Token
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

    # Sende Email
    try:
        send_magic_link_email(email, token, 'login')
    except Exception as e:
        current_app.logger.error(f"Email-Versand fehlgeschlagen: {str(e)}")
        return jsonify({'error': 'Email konnte nicht gesendet werden'}), 500

    current_app.logger.info(f"[LOGIN] Magic Link gesendet an {email}")

    return jsonify({
        'message': 'Login-Link wurde an deine Email gesendet. Bitte ueberprueafe dein Postfach.'
    }), 200


@api_bp.route('/auth/signup', methods=['POST'])
def api_signup():
    """API-Registrierung mit Magic Link (Passwordless)"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten uebermittelt'}), 400

    email = data.get('email', '').strip().lower()

    # Validierung
    if not email:
        return jsonify({'error': 'Email ist erforderlich'}), 400

    # Email-Format prüfen (einfache Regex)
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': 'Ungueltige Email-Adresse'}), 400

    # Prüfe ob Email bereits registriert
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        # Statt Fehler: Sende Login-Link (bessere UX, verhindert User-Enumeration)
        if existing_user.is_blocked:
            return jsonify({'error': 'Dein Account wurde gesperrt'}), 403

        # Rate-Limiting prüfen
        if not check_rate_limit(email):
            return jsonify({'error': 'Zu viele Anfragen. Bitte versuche es später erneut.'}), 429

        # Generiere Magic Link Token für Login
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

        # Sende Email
        try:
            send_magic_link_email(email, token, 'login')
        except Exception as e:
            current_app.logger.error(f"Email-Versand fehlgeschlagen: {str(e)}")
            return jsonify({'error': 'Email konnte nicht gesendet werden'}), 500

        current_app.logger.info(f"[SIGNUP] Email {email} existiert bereits - Login-Link gesendet")

        # Gleiche Nachricht wie bei Neuregistrierung (verhindert User-Enumeration)
        return jsonify({
            'message': 'Registrierungs-Link wurde an deine Email gesendet. Bitte überprüfe dein Postfach.'
        }), 200

    # Rate-Limiting
    if not check_rate_limit(email):
        return jsonify({'error': 'Zu viele Anfragen. Bitte versuche es später erneut.'}), 429

    # Erstelle User (initial mit status=REGISTERED)
    slug = generate_slug_from_email(email)

    # Prüfe ob Slug bereits existiert (unwahrscheinlich, aber möglich)
    slug_exists = User.query.filter_by(slug=slug).first()
    if slug_exists:
        # Füge Random-Suffix hinzu
        slug = slug + generate_magic_link_token()[:4]

    # Prüfe ob dies der erste User ist -> wird Admin
    is_first_user = User.query.count() == 0

    user = User(email=email, slug=slug)
    user.state = UserState.REGISTERED.value
    user.is_admin = is_first_user
    db.session.add(user)
    db.session.flush()  # Damit user.id verfügbar ist

    # Generiere Magic Link Token
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

    # Sende Email
    try:
        send_magic_link_email(email, token, 'signup')
    except Exception as e:
        current_app.logger.error(f"Email-Versand fehlgeschlagen: {str(e)}")
        # Cleanup: Lösche User und Token
        db.session.delete(magic_token)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'error': 'Email konnte nicht gesendet werden'}), 500

    current_app.logger.info(f"[SIGNUP] Magic Link gesendet an {email}")

    return jsonify({
        'message': 'Registrierungs-Link wurde an deine Email gesendet. Bitte überprüfe dein Postfach.'
    }), 200


@api_bp.route('/auth/verify-signup', methods=['GET'])
def api_verify_signup():
    """Verifiziert Signup Magic Link und erstellt JWT"""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token fehlt'}), 400

    # Suche Token in Datenbank
    magic_token = MagicLinkToken.query.filter_by(
        token=token,
        token_type='signup'
    ).first()

    if not magic_token:
        return jsonify({'error': 'Ungültiger oder abgelaufener Link'}), 400

    # Prüfe Gültigkeit
    if not magic_token.is_valid():
        return jsonify({'error': 'Dieser Link ist abgelaufen oder wurde bereits verwendet'}), 400

    # Hole User
    user = magic_token.user

    # Setze User-Status auf VERIFIED
    user.state = UserState.VERIFIED.value
    magic_token.mark_as_used()
    db.session.commit()

    # Container spawnen (nur beim ersten Signup) - Multi-Container kompatibel
    if not user.container_id:
        try:
            container_mgr = ContainerManager()
            # Nutze spawn_multi_container mit Standard-Template (template-01)
            default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
            container_id, port = container_mgr.spawn_multi_container(
                user.id,
                user.slug,
                default_template
            )
            # Speichere in Primary Container (backwards compatibility)
            if user.containers:
                user.containers[0].container_id = container_id
                user.containers[0].container_port = port
            db.session.commit()
            current_app.logger.info(f"[SPAWNER] Container {default_template} erstellt für User {user.id} (slug: {user.slug})")
        except Exception as e:
            current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(e)}")
            # Notiere: Container-Spawn ist optional beim Signup
            # User ist trotzdem erstellt, Container kann später manuell erstellt werden

    # JWT erstellen
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'is_admin': user.is_admin}
    )

    current_app.logger.info(f"[SIGNUP] User {user.email} erfolgreich registriert")

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(expires.total_seconds()),
        'user': {
            'id': user.id,
            'email': user.email,
            'slug': user.slug,
            'is_admin': user.is_admin,
            'state': user.state,
            'container_id': user.container_id
        }
    }), 200


@api_bp.route('/auth/verify-login', methods=['GET'])
def api_verify_login():
    """Verifiziert Login Magic Link und erstellt JWT"""
    token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token fehlt'}), 400

    # Suche Token
    magic_token = MagicLinkToken.query.filter_by(
        token=token,
        token_type='login'
    ).first()

    if not magic_token:
        return jsonify({'error': 'Ungültiger oder abgelaufener Link'}), 400

    # Prüfe Gültigkeit
    if not magic_token.is_valid():
        return jsonify({'error': 'Dieser Link ist abgelaufen oder wurde bereits verwendet'}), 400

    # Hole User
    user = magic_token.user

    # Prüfe ob User blockiert
    if user.is_blocked:
        return jsonify({'error': 'Dein Account wurde gesperrt'}), 403

    # Prüfe ob Email verifiziert
    if user.state == UserState.REGISTERED.value:
        return jsonify({'error': 'Bitte verifiziere zuerst deine Email-Adresse'}), 403

    # Markiere Token als verwendet
    magic_token.mark_as_used()

    # Container Management - starten oder neu erstellen
    container_mgr = ContainerManager()

    if user.container_id:
        try:
            status = container_mgr.get_container_status(user.container_id)
            if status != 'running':
                # Container neu starten
                container_mgr.start_container(user.container_id)
                current_app.logger.info(f"[LOGIN] Container {user.container_id[:12]} neu gestartet für User {user.email}")
        except Exception as e:
            # Container existiert nicht mehr - neuen erstellen
            current_app.logger.warning(f"Container {user.container_id[:12]} nicht gefunden, erstelle neuen: {str(e)}")
            try:
                # Nutze spawn_multi_container für Primary Container
                default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
                container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
                if user.containers:
                    user.containers[0].container_id = container_id
                    user.containers[0].container_port = port
                current_app.logger.info(f"[LOGIN] Neuer Container {default_template} erstellt für User {user.email} (slug: {user.slug})")
            except Exception as spawn_error:
                current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(spawn_error)}")
    else:
        # Kein Container vorhanden - neu erstellen
        try:
            # Nutze spawn_multi_container für Primary Container
            default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
            container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
            if user.containers:
                user.containers[0].container_id = container_id
                user.containers[0].container_port = port
            current_app.logger.info(f"[LOGIN] Container erstellt für User {user.email} (slug: {user.slug})")
        except Exception as e:
            current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(e)}")

    user.last_used = datetime.utcnow()
    db.session.commit()

    # JWT erstellen
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'is_admin': user.is_admin}
    )

    current_app.logger.info(f"[LOGIN] User {user.email} erfolgreich eingeloggt")

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(expires.total_seconds()),
        'user': {
            'id': user.id,
            'email': user.email,
            'slug': user.slug,
            'is_admin': user.is_admin,
            'state': user.state,
            'container_id': user.container_id
        }
    }), 200


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """API-Logout - invalidiert Token"""
    jti = get_jwt()['jti']
    token_blacklist.add(jti)
    return jsonify({'message': 'Erfolgreich abgemeldet'}), 200


@api_bp.route('/user/me', methods=['GET'])
@jwt_required()
def api_user_me():
    """Gibt aktuellen User und Container-Info zurueck"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    # Service-URL berechnen
    scheme = current_app.config['PREFERRED_URL_SCHEME']
    spawner_domain = f"{current_app.config['SPAWNER_SUBDOMAIN']}.{current_app.config['BASE_DOMAIN']}"
    service_url = f"{scheme}://{spawner_domain}/{user.slug}"

    # Container-Status abrufen
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
    """Gibt Container-Status zurück"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

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
    """Startet Container neu"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    container_mgr = ContainerManager()

    # Alten Container stoppen falls vorhanden
    if user.container_id:
        try:
            container_mgr.stop_container(user.container_id)
            container_mgr.remove_container(user.container_id)
        except Exception as e:
            current_app.logger.warning(f"Alter Container konnte nicht gestoppt werden: {str(e)}")

    # Neuen Container starten - Multi-Container kompatibel
    try:
        # Nutze spawn_multi_container für Primary Container
        default_template = list(current_app.config['CONTAINER_TEMPLATES'].keys())[0]
        container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, default_template)
        if user.containers:
            user.containers[0].container_id = container_id
            user.containers[0].container_port = port

        # State auf ACTIVE setzen bei Container-Start (falls noch VERIFIED)
        if user.state == UserState.VERIFIED.value:
            user.state = UserState.ACTIVE.value

        # last_used aktualisieren
        user.last_used = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Container erfolgreich neugestartet',
            'container_id': container_id,
            'status': 'running'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Container-Restart fehlgeschlagen: {str(e)}")
        return jsonify({'error': f'Container-Restart fehlgeschlagen: {str(e)}'}), 500


def check_if_token_revoked(jwt_header, jwt_payload):
    """Callback für flask-jwt-extended um revoked Tokens zu prüfen"""
    jti = jwt_payload['jti']
    return jti in token_blacklist


# ============================================================
# Multi-Container Support Endpoints
# ============================================================

@api_bp.route('/user/containers', methods=['GET'])
@jwt_required()
def api_user_containers():
    """Gibt alle Container des Users zurück"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    # Container-Liste erstellen
    containers = []
    for container_type, template in current_app.config['CONTAINER_TEMPLATES'].items():
        # Suche existierenden Container
        user_container = UserContainer.query.filter_by(
            user_id=user.id,
            container_type=container_type
        ).first()

        # Service-URL
        scheme = current_app.config['PREFERRED_URL_SCHEME']
        spawner_domain = f"{current_app.config['SPAWNER_SUBDOMAIN']}.{current_app.config['BASE_DOMAIN']}"
        slug_with_suffix = f"{user.slug}-{container_type}"
        service_url = f"{scheme}://{spawner_domain}/{slug_with_suffix}"

        # Status ermitteln
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
            'last_used': user_container.last_used.isoformat() if user_container and user_container.last_used else None
        })

    return jsonify({'containers': containers}), 200


@api_bp.route('/container/launch/<container_type>', methods=['POST'])
@jwt_required()
def api_container_launch(container_type):
    """Erstellt Container on-demand und gibt Service-URL zurück"""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({'error': 'User nicht gefunden'}), 404

    # Prüfe ob Typ valide
    if container_type not in current_app.config['CONTAINER_TEMPLATES']:
        return jsonify({'error': f'Ungültiger Container-Typ: {container_type}'}), 400

    # Prüfe ob Container bereits existiert
    user_container = UserContainer.query.filter_by(
        user_id=user.id,
        container_type=container_type
    ).first()

    container_mgr = ContainerManager()

    if user_container and user_container.container_id:
        # Container existiert - Status prüfen
        try:
            status = container_mgr.get_container_status(user_container.container_id)
            if status != 'running':
                # Container neu starten
                container_mgr.start_container(user_container.container_id)
                current_app.logger.info(f"[MULTI-CONTAINER] Container {user_container.container_id[:12]} neu gestartet")

            # last_used aktualisieren
            user_container.last_used = datetime.utcnow()
            db.session.commit()

        except Exception as e:
            # Container existiert nicht mehr - neu erstellen
            current_app.logger.warning(f"Container {user_container.container_id[:12]} nicht gefunden, erstelle neuen: {str(e)}")
            try:
                template = current_app.config['CONTAINER_TEMPLATES'][container_type]
                container_id, port = container_mgr.spawn_multi_container(user.id, user.slug, container_type)
                user_container.container_id = container_id
                user_container.container_port = port
                user_container.last_used = datetime.utcnow()
                db.session.commit()
                current_app.logger.info(f"[MULTI-CONTAINER] Neuer {container_type} Container erstellt für {user.email}")
            except Exception as spawn_error:
                current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(spawn_error)}")
                return jsonify({'error': 'Container konnte nicht erstellt werden'}), 500
    else:
        # Container existiert noch nicht - neu erstellen
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

            current_app.logger.info(f"[MULTI-CONTAINER] {container_type} Container erstellt für {user.email}")
        except Exception as e:
            current_app.logger.error(f"Container-Spawn fehlgeschlagen: {str(e)}")
            return jsonify({'error': f'Container konnte nicht erstellt werden: {str(e)}'}), 500

    # Service-URL generieren
    scheme = current_app.config['PREFERRED_URL_SCHEME']
    spawner_domain = f"{current_app.config['SPAWNER_SUBDOMAIN']}.{current_app.config['BASE_DOMAIN']}"
    slug_with_suffix = f"{user.slug}-{container_type}"
    service_url = f"{scheme}://{spawner_domain}/{slug_with_suffix}"

    return jsonify({
        'message': 'Container bereit',
        'service_url': service_url,
        'container_id': user_container.container_id,
        'status': 'running'
    }), 200
