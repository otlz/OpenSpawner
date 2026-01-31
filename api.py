from flask import Blueprint, jsonify, request, current_app, redirect
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta, datetime
from models import db, User, UserState
from container_manager import ContainerManager
from email_service import generate_verification_token, send_verification_email
from config import Config

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Token-Blacklist für Logout
token_blacklist = set()


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API-Login - gibt JWT-Token zurueck"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten uebermittelt'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username und Passwort erforderlich'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Ungueltige Anmeldedaten'}), 401

    # Blockade-Check
    if user.is_blocked:
        return jsonify({'error': 'Konto gesperrt. Kontaktiere einen Administrator.'}), 403

    # Verifizierungs-Check
    if user.state == UserState.REGISTERED.value:
        return jsonify({
            'error': 'Email nicht verifiziert. Bitte pruefe dein Postfach.',
            'needs_verification': True
        }), 403

    # Container spawnen wenn noch nicht vorhanden
    if not user.container_id:
        try:
            container_mgr = ContainerManager()
            container_id, port = container_mgr.spawn_container(user.id, user.username)
            user.container_id = container_id
            user.container_port = port
            # State auf ACTIVE setzen bei erstem Container-Start
            if user.state == UserState.VERIFIED.value:
                user.state = UserState.ACTIVE.value
            user.last_used = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Container-Start fehlgeschlagen: {str(e)}")
            return jsonify({'error': f'Container-Start fehlgeschlagen: {str(e)}'}), 500
    else:
        # last_used aktualisieren
        user.last_used = datetime.utcnow()
        db.session.commit()

    # JWT-Token erstellen
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'username': user.username, 'is_admin': user.is_admin}
    )

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(expires.total_seconds()),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'state': user.state
        }
    }), 200


@api_bp.route('/auth/signup', methods=['POST'])
def api_signup():
    """API-Registrierung - erstellt User und sendet Verifizierungs-Email"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten uebermittelt'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, Email und Passwort erforderlich'}), 400

    # Validierung
    if len(username) < 3:
        return jsonify({'error': 'Username muss mindestens 3 Zeichen lang sein'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Passwort muss mindestens 6 Zeichen lang sein'}), 400

    # Username-Validierung (nur alphanumerisch und Bindestrich)
    import re
    if not re.match(r'^[a-zA-Z0-9-]+$', username):
        return jsonify({'error': 'Username darf nur Buchstaben, Zahlen und Bindestriche enthalten'}), 400

    # Pruefe ob User existiert
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username bereits vergeben'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email bereits registriert'}), 409

    # Pruefe ob dies der erste User ist -> wird Admin
    is_first_user = User.query.count() == 0

    # Neuen User anlegen
    user = User(username=username, email=email)
    user.set_password(password)
    user.is_admin = is_first_user
    user.state = UserState.REGISTERED.value
    user.verification_token = generate_verification_token()
    user.verification_sent_at = datetime.utcnow()

    db.session.add(user)
    db.session.commit()

    # Verifizierungs-Email senden
    frontend_url = Config.FRONTEND_URL
    email_sent = send_verification_email(
        user.email,
        user.username,
        user.verification_token,
        frontend_url
    )

    if not email_sent:
        current_app.logger.warning(f"Verifizierungs-Email konnte nicht gesendet werden an {user.email}")

    return jsonify({
        'message': 'Registrierung erfolgreich. Bitte pruefe dein Postfach und bestatige deine Email-Adresse.',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin
        },
        'email_sent': email_sent
    }), 201


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def api_logout():
    """API-Logout - invalidiert Token"""
    jti = get_jwt()['jti']
    token_blacklist.add(jti)
    return jsonify({'message': 'Erfolgreich abgemeldet'}), 200


@api_bp.route('/auth/verify', methods=['GET'])
def api_verify_email():
    """Email-Verifizierung ueber Token-Link"""
    token = request.args.get('token')
    frontend_url = Config.FRONTEND_URL

    if not token:
        return redirect(f"{frontend_url}/verify-error?reason=missing_token")

    user = User.query.filter_by(verification_token=token).first()

    if not user:
        return redirect(f"{frontend_url}/verify-error?reason=invalid_token")

    # Token invalidieren und Status aktualisieren
    user.verification_token = None
    user.state = UserState.VERIFIED.value
    db.session.commit()

    current_app.logger.info(f"User {user.username} hat Email verifiziert")
    return redirect(f"{frontend_url}/verify-success?verified=true")


@api_bp.route('/auth/resend-verification', methods=['POST'])
def api_resend_verification():
    """Sendet Verifizierungs-Email erneut"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten uebermittelt'}), 400

    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email erforderlich'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        # Aus Sicherheitsgruenden kein Fehler wenn User nicht existiert
        return jsonify({'message': 'Falls die Email registriert ist, wurde eine neue Verifizierungs-Email gesendet.'}), 200

    if user.state != UserState.REGISTERED.value:
        return jsonify({'error': 'Email bereits verifiziert'}), 400

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

    return jsonify({
        'message': 'Falls die Email registriert ist, wurde eine neue Verifizierungs-Email gesendet.',
        'email_sent': email_sent
    }), 200


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
    service_url = f"{scheme}://{spawner_domain}/{user.username}"

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
            'username': user.username,
            'email': user.email,
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

    # Neuen Container starten
    try:
        container_id, port = container_mgr.spawn_container(user.id, user.username)
        user.container_id = container_id
        user.container_port = port

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
