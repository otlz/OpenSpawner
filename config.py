import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ========================================
    # Sicherheit
    # ========================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # JWT-Konfiguration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 Stunde
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # CORS-Konfiguration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Session-Sicherheit
    SESSION_COOKIE_SECURE = os.getenv('BASE_DOMAIN', 'localhost') != 'localhost'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 Stunde
    
    # ========================================
    # Datenbank
    # ========================================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:////app/data/users.db'  # 4 slashes: sqlite:// + /app/data/users.db
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ========================================
    # Docker-Konfiguration
    # ========================================
    DOCKER_SOCKET = os.getenv('DOCKER_SOCKET', 'unix://var/run/docker.sock')
    USER_TEMPLATE_IMAGE = os.getenv('USER_TEMPLATE_IMAGE', 'user-service-template:latest')
    
    # ========================================
    # Traefik/Domain-Konfiguration
    # ========================================
    BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'localhost')
    SPAWNER_SUBDOMAIN = os.getenv('SPAWNER_SUBDOMAIN', 'spawner')
    TRAEFIK_NETWORK = os.getenv('TRAEFIK_NETWORK', 'web')
    TRAEFIK_CERTRESOLVER = os.getenv('TRAEFIK_CERTRESOLVER', 'lets-encrypt')
    TRAEFIK_ENTRYPOINT = os.getenv('TRAEFIK_ENTRYPOINT', 'websecure')

    # Vollständige Spawner-URL
    SPAWNER_URL = f"{SPAWNER_SUBDOMAIN}.{BASE_DOMAIN}"
    
    # ========================================
    # Application-Settings
    # ========================================
    # HTTPS automatisch für Nicht-Localhost
    PREFERRED_URL_SCHEME = 'https' if BASE_DOMAIN != 'localhost' else 'http'
    
    # Spawner-Port (nur für Debugging wichtig)
    SPAWNER_PORT = int(os.getenv('SPAWNER_PORT', 5000))
    
    # ========================================
    # Optionale Einstellungen
    # ========================================
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/spawner.log')
    
    # Container-Limits (für container_manager.py)
    DEFAULT_MEMORY_LIMIT = os.getenv('DEFAULT_MEMORY_LIMIT', '512m')
    DEFAULT_CPU_QUOTA = int(os.getenv('DEFAULT_CPU_QUOTA', 50000))  # 0.5 CPU
    
    # Container-Cleanup
    CONTAINER_IDLE_TIMEOUT = int(os.getenv('CONTAINER_IDLE_TIMEOUT', 3600))  # 1h in Sekunden

    # ========================================
    # SMTP / Email-Konfiguration
    # ========================================
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'noreply@localhost')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    # Frontend-URL fuer Email-Links
    FRONTEND_URL = os.getenv(
        'FRONTEND_URL',
        f"{PREFERRED_URL_SCHEME}://{SPAWNER_SUBDOMAIN}.{BASE_DOMAIN}"
    )

    # ========================================
    # Magic Link Passwordless Auth
    # ========================================
    MAGIC_LINK_TOKEN_EXPIRY = int(os.getenv('MAGIC_LINK_TOKEN_EXPIRY', 900))  # 15 Minuten
    MAGIC_LINK_RATE_LIMIT = int(os.getenv('MAGIC_LINK_RATE_LIMIT', 3))  # Max 3 pro Stunde


class DevelopmentConfig(Config):
    """Konfiguration für Entwicklung"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Konfiguration für Produktion"""
    DEBUG = False
    TESTING = False
    
    # Strikte Session-Sicherheit
    SESSION_COOKIE_SECURE = True
    
    # Optional: PostgreSQL statt SQLite
    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     'DATABASE_URL',
    #     'postgresql://spawner:password@postgres:5432/spawner'
    # )


class TestingConfig(Config):
    """Konfiguration für Tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Config-Dict für einfaches Laden
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
