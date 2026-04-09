from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, login_required, current_user
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy import text
from models import db, User, AdminTakeoverSession
from auth import auth_bp
from api import api_bp, check_if_token_revoked
from admin_api import admin_bp
from config import Config
from container_manager import ContainerManager
import logging
from logging.handlers import RotatingFileHandler
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize CORS
CORS(app, resources={
    r"/api/*": {
        "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize JWT
jwt = JWTManager(app)

# Initialize Swagger/OpenAPI
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'openapi',
            "route": '/openapi.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger",
    "title": "OpenSpawner API",
    "description": "REST API for OpenSpawner with admin debug endpoints",
    "version": "2.0.0",
    "termsOfService": "",
    "contact": {
        "name": "API Support"
    }
}
swagger = Swagger(app, config=swagger_config)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    return check_if_token_revoked(jwt_header, jwt_payload)

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authentication required'}), 401

# ========================================
# Configure logging
# ========================================
log_file = app.config.get('LOG_FILE', '/app/logs/spawner.log')
log_dir = os.path.dirname(log_file)

# Create log directory if it doesn't exist
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

# Rotating File Handler (max 10MB per file, 5 backups)
if log_file:
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'error'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))

@app.route('/')
def index():
    """Homepage - redirect to dashboard or login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - shows container status and service URL"""
    container_mgr = ContainerManager()
    container_status = 'unknown'

    if current_user.container_id:
        container_status = container_mgr.get_container_status(current_user.container_id)

    # Service URL for user (path-based)
    scheme = app.config['PREFERRED_URL_SCHEME']
    spawner_domain = f"{app.config['SPAWNER_SUBDOMAIN']}.{app.config['BASE_DOMAIN']}"
    service_url = f"{scheme}://{spawner_domain}/{current_user.slug}"

    return render_template('dashboard.html',
                         user=current_user,
                         service_url=service_url,
                         container_status=container_status)

@app.route('/container/restart')
@login_required
def restart_container():
    """Restart user's container"""
    container_mgr = ContainerManager()
    
    # Stop old container if exists
    if current_user.container_id:
        container_mgr.stop_container(current_user.container_id)
        container_mgr.remove_container(current_user.container_id)
    
    # Start new container - multi-container compatible
    try:
        # Use spawn_multi_container for primary container
        default_template = list(app.config['CONTAINER_TEMPLATES'].keys())[0]
        container_id, port = container_mgr.spawn_multi_container(current_user.id, current_user.slug, default_template)
        if current_user.containers:
            current_user.containers[0].container_id = container_id
            current_user.containers[0].container_port = port
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Container restart failed: {str(e)}")
    
    return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Health check for Docker and monitoring"""
    db_status = 'ok'
    docker_status = 'warning'

    try:
        # DB check (CRITICAL)
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        db_status = f'error: {str(e)}'
        app.logger.error(f"Database health check failed: {str(e)}")

    try:
        # Docker check (OPTIONAL)
        container_mgr = ContainerManager()
        container_mgr._get_client().ping()
        docker_status = 'ok'
    except Exception as e:
        docker_status = f'warning: {str(e)}'
        app.logger.warning(f"Docker health check failed (non-critical): {str(e)}")

    # Return 503 only if DATABASE is down, not if Docker is down
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

# Create database tables on first start
with app.app_context():
    db.create_all()
    app.logger.info('Database tables created')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
