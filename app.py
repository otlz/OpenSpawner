from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from sqlalchemy import text
from models import db, User, AdminTakeoverSession
from auth import auth_bp
from api import api_bp, check_if_token_revoked
from admin_api import admin_bp
from config import Config
from container_manager import ContainerManager

# Flask-App initialisieren
app = Flask(__name__)
app.config.from_object(Config)

# Datenbank initialisieren
db.init_app(app)

# CORS initialisieren
CORS(app, resources={
    r"/api/*": {
        "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# JWT initialisieren
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return check_if_token_revoked(jwt_header, jwt_payload)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token abgelaufen'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Ungültiger Token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authentifizierung erforderlich'}), 401

# Flask-Login initialisieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bitte melde dich an, um auf diese Seite zuzugreifen.'
login_manager.login_message_category = 'error'

# Blueprints registrieren
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

@login_manager.user_loader
def load_user(user_id):
    """Lädt User für Flask-Login"""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Startseite - Redirect zu Dashboard oder Login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - zeigt Container-Status und Service-URL"""
    container_mgr = ContainerManager()
    container_status = 'unknown'

    if current_user.container_id:
        container_status = container_mgr.get_container_status(current_user.container_id)

    # Service-URL für den User (pfad-basiert)
    scheme = app.config['PREFERRED_URL_SCHEME']
    spawner_domain = f"{app.config['SPAWNER_SUBDOMAIN']}.{app.config['BASE_DOMAIN']}"
    service_url = f"{scheme}://{spawner_domain}/{current_user.username}"

    return render_template('dashboard.html',
                         user=current_user,
                         service_url=service_url,
                         container_status=container_status)

@app.route('/container/restart')
@login_required
def restart_container():
    """Startet Container des Users neu"""
    container_mgr = ContainerManager()
    
    # Alten Container stoppen falls vorhanden
    if current_user.container_id:
        container_mgr.stop_container(current_user.container_id)
        container_mgr.remove_container(current_user.container_id)
    
    # Neuen Container starten
    try:
        container_id, port = container_mgr.spawn_container(current_user.id, current_user.username)
        current_user.container_id = container_id
        current_user.container_port = port
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Container-Restart fehlgeschlagen: {str(e)}")
    
    return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Health-Check für Docker und Monitoring"""
    db_status = 'ok'
    docker_status = 'warning'

    try:
        # DB-Check (KRITISCH)
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        db_status = f'error: {str(e)}'
        app.logger.error(f"Database health check failed: {str(e)}")

    try:
        # Docker-Check (OPTIONAL)
        container_mgr = ContainerManager()
        container_mgr._get_client().ping()
        docker_status = 'ok'
    except Exception as e:
        docker_status = f'warning: {str(e)}'
        app.logger.warning(f"Docker health check failed (non-critical): {str(e)}")

    # Status 503 nur wenn DATABASE down ist, nicht wenn Docker down ist
    status_code = 200 if db_status == 'ok' else 503

    response = {
        'status': 'healthy' if status_code == 200 else 'unhealthy',
        'database': db_status,
        'docker': docker_status,
        'version': '1.0.0'
    }

    if status_code != 200:
        app.logger.error(f"Health check CRITICAL: {response}")
    else:
        app.logger.info(f"Health check OK")

    return response, status_code

# Datenbank-Tabellen erstellen beim ersten Start
with app.app_context():
    db.create_all()
    app.logger.info('Datenbank-Tabellen erstellt')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
