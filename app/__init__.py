from flask import Flask, jsonify
from flask_cors import CORS
from flasgger import Swagger
from sqlalchemy import text
from app.extensions import db, login_manager, jwt
from app.models import User
from app.routes.auth import auth_bp
from app.routes.api import api_bp, check_if_token_revoked
from app.routes.admin import admin_bp
from app.services.container_manager import ContainerManager
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os


def create_app():
    """Flask application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'
    jwt.init_app(app)

    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', ['http://localhost:3000']),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

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
    Swagger(app, config=swagger_config)

    # JWT callbacks
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

    # Configure logging
    log_file = app.config.get('LOG_FILE', '/app/logs/spawner.log')
    log_dir = os.path.dirname(log_file)

    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

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

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Health check route
    @app.route('/health')
    def health():
        """Health check for Docker and monitoring"""
        db_status = 'ok'
        docker_status = 'warning'

        try:
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            db_status = f'error: {str(e)}'
            app.logger.error(f"Database health check failed: {str(e)}")

        try:
            container_mgr = ContainerManager()
            container_mgr._get_client().ping()
            docker_status = 'ok'
        except Exception as e:
            docker_status = f'warning: {str(e)}'
            app.logger.warning(f"Docker health check failed (non-critical): {str(e)}")

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

    return app
