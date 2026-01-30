from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from datetime import timedelta
from models import db, User
from container_manager import ContainerManager

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Token-Blacklist für Logout
token_blacklist = set()


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """API-Login - gibt JWT-Token zurück"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten übermittelt'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username und Passwort erforderlich'}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Ungültige Anmeldedaten'}), 401

    # Container spawnen wenn noch nicht vorhanden
    if not user.container_id:
        try:
            container_mgr = ContainerManager()
            container_id, port = container_mgr.spawn_container(user.id, user.username)
            user.container_id = container_id
            user.container_port = port
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Container-Start fehlgeschlagen: {str(e)}")
            return jsonify({'error': f'Container-Start fehlgeschlagen: {str(e)}'}), 500

    # JWT-Token erstellen
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'username': user.username}
    )

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(expires.total_seconds()),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200


@api_bp.route('/auth/signup', methods=['POST'])
def api_signup():
    """API-Registrierung - erstellt User, spawnt Container, gibt JWT zurück"""
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Keine Daten übermittelt'}), 400

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

    # Prüfe ob User existiert
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username bereits vergeben'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email bereits registriert'}), 409

    # Neuen User anlegen
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Container spawnen
    try:
        container_mgr = ContainerManager()
        container_id, port = container_mgr.spawn_container(user.id, user.username)
        user.container_id = container_id
        user.container_port = port
        db.session.commit()
    except Exception as e:
        db.session.delete(user)
        db.session.commit()
        current_app.logger.error(f"Registrierung fehlgeschlagen: {str(e)}")
        return jsonify({'error': f'Container-Erstellung fehlgeschlagen: {str(e)}'}), 500

    # JWT-Token erstellen
    expires = timedelta(seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=expires,
        additional_claims={'username': user.username}
    )

    return jsonify({
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': int(expires.total_seconds()),
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201


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
    """Gibt aktuellen User und Container-Info zurück"""
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
