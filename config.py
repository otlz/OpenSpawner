"""
Konfiguration für OpenSpawner.
Alle Umgebungsvariablen sind in .env.example dokumentiert.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ========================================
    # Sicherheit
    # ========================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_TOKEN_LOCATION = ['cookies', 'headers']
    JWT_ACCESS_COOKIE_NAME = 'spawner_token'
    JWT_COOKIE_CSRF_PROTECT = False  # SameSite=Strict handles CSRF
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    # Session security
    SESSION_COOKIE_SECURE = os.getenv('BASE_DOMAIN', 'localhost') != 'localhost'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # ========================================
    # Database
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

    # Legacy-Fallback für Backward-Kompatibilität (models.py)
    USER_TEMPLATE_IMAGE = os.getenv('USER_TEMPLATE_IMAGE', 'template-nginx:latest')

    # Wartezeit nach Container-Start (Sekunden)
    CONTAINER_STARTUP_WAIT = int(os.getenv('CONTAINER_STARTUP_WAIT', 2))

    # ========================================
    # Dynamisches Template-System
    # ========================================

    # Werden von init_templates() befuellt
    TEMPLATE_IMAGES = None
    TEMPLATES_CONFIG = None
    CONTAINER_TEMPLATES = None

    @staticmethod
    def _extract_type_from_image(image_name: str) -> str:
        """Extrahiert den Container-Typ aus dem Image-Namen (z.B. 'template-nginx:latest' -> 'template-nginx')."""
        return image_name.split(':')[0]

    @staticmethod
    def _load_template_images() -> list:
        """Lädt die Template-Image-Liste aus USER_TEMPLATE_IMAGES (Semikolon-getrennt)."""
        raw_images = os.getenv('USER_TEMPLATE_IMAGES', '')
        if not raw_images:
            return ['template-nginx:latest']
        return [img.strip() for img in raw_images.split(';') if img.strip()]

    @staticmethod
    def _load_templates_config() -> tuple:
        """Lädt Template-Metadaten und Kategorien aus templates.json."""
        config_path = Path(__file__).parent / 'templates.json'
        if not config_path.exists():
            return {}, []
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            templates = {t['type']: t for t in data.get('templates', [])}
            categories = data.get('categories', [])
            return templates, categories
        except (json.JSONDecodeError, KeyError) as e:
            import sys
            print(f"[CONFIG] Warning: Error loading templates.json: {e}", file=sys.stderr)
            return {}, []

    @classmethod
    def init_templates(cls):
        """
        Lädt Container-Templates aus templates.json (alle verfügbaren Templates).
        Fällt auf USER_TEMPLATE_IMAGES zurück, falls templates.json fehlt.
        """
        cls.TEMPLATES_CONFIG, cls.TEMPLATE_CATEGORIES = cls._load_templates_config()

        templates = {}

        if cls.TEMPLATES_CONFIG:
            # Primär: Alle Templates aus templates.json laden
            for container_type, config_meta in cls.TEMPLATES_CONFIG.items():
                image = config_meta.get('image', f'{container_type}:latest')
                templates[container_type] = {
                    'image': image,
                    'display_name': config_meta.get('display_name', container_type.replace('-', ' ').title()),
                    'description': config_meta.get('description', f'Container basierend auf {image}'),
                    'os': config_meta.get('os', 'Linux'),
                    'software': config_meta.get('software', ''),
                    'icon': config_meta.get('icon', ''),
                    'port': config_meta.get('port', 8080),
                    'volumes': config_meta.get('volumes', []),
                    'memory_limit': config_meta.get('memory_limit', cls.DEFAULT_MEMORY_LIMIT),
                    'cpu_quota': config_meta.get('cpu_quota', cls.DEFAULT_CPU_QUOTA),
                    'pids_limit': config_meta.get('pids_limit', 100),
                    'cap_add': config_meta.get('cap_add', []),
                    'category': config_meta.get('category', 'software'),
                }
        else:
            # Fallback: USER_TEMPLATE_IMAGES aus .env
            cls.TEMPLATE_IMAGES = cls._load_template_images()
            for image in cls.TEMPLATE_IMAGES:
                container_type = cls._extract_type_from_image(image)
                templates[container_type] = {
                    'image': image,
                    'display_name': container_type.replace('-', ' ').title(),
                    'description': f'Container basierend auf {image}',
                    'os': 'Linux',
                    'software': '',
                    'icon': '',
                    'port': 8080,
                    'volumes': [],
                    'memory_limit': cls.DEFAULT_MEMORY_LIMIT,
                    'cpu_quota': cls.DEFAULT_CPU_QUOTA,
                    'pids_limit': 100,
                    'cap_add': [],
                    'category': 'software',
                }

        cls.CONTAINER_TEMPLATES = templates

    # ========================================
    # Traefik / Domain Configuration
    # ========================================
    BASE_DOMAIN = os.getenv('BASE_DOMAIN', 'localhost')
    SPAWNER_SUBDOMAIN = os.getenv('SPAWNER_SUBDOMAIN', 'spawner')
    TRAEFIK_NETWORK = os.getenv('TRAEFIK_NETWORK', 'web')
    TRAEFIK_CERTRESOLVER = os.getenv('TRAEFIK_CERTRESOLVER', 'lets-encrypt')
    TRAEFIK_ENTRYPOINT = os.getenv('TRAEFIK_ENTRYPOINT', 'websecure')

    # Traefik mode toggle (auto-detects based on BASE_DOMAIN)
    TRAEFIK_ENABLED = os.getenv(
        'TRAEFIK_ENABLED',
        str(os.getenv('BASE_DOMAIN', 'localhost') != 'localhost')
    ).lower() == 'true'

    # Network for spawned user containers
    CONTAINER_NETWORK = os.getenv('CONTAINER_NETWORK', TRAEFIK_NETWORK if os.getenv(
        'TRAEFIK_ENABLED',
        str(os.getenv('BASE_DOMAIN', 'localhost') != 'localhost')
    ).lower() == 'true' else 'openspawner_openspawner')

    # Full spawner URL
    SPAWNER_URL = f"{SPAWNER_SUBDOMAIN}.{BASE_DOMAIN}"

    # ========================================
    # Application Settings
    # ========================================
    # HTTPS automatically for non-localhost
    PREFERRED_URL_SCHEME = 'https' if BASE_DOMAIN != 'localhost' else 'http'

    # Spawner port (only relevant for debugging)
    SPAWNER_PORT = int(os.getenv('SPAWNER_PORT', 5000))

    # ========================================
    # Optional Settings
    # ========================================
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', '/app/logs/spawner.log')

    # Container limits (for container_manager.py)
    DEFAULT_MEMORY_LIMIT = os.getenv('DEFAULT_MEMORY_LIMIT', '512m')
    DEFAULT_CPU_QUOTA = int(os.getenv('DEFAULT_CPU_QUOTA', 50000))  # 0.5 CPU

    # Container lifecycle
    CONTAINER_IDLE_TIMEOUT = int(os.getenv('CONTAINER_IDLE_TIMEOUT', 3600))  # 1h -> stop
    CONTAINER_STALE_TIMEOUT = int(os.getenv('CONTAINER_STALE_TIMEOUT', 604800))  # 7 days -> remove (keep volumes)
    REAPER_INTERVAL = int(os.getenv('REAPER_INTERVAL', 60))  # Check every 60s

    # ========================================
    # SMTP / Email Configuration
    # ========================================
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM = os.getenv('SMTP_FROM', 'noreply@localhost')
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'

    # Frontend URL for email links
    FRONTEND_URL = os.getenv(
        'FRONTEND_URL',
        f"{PREFERRED_URL_SCHEME}://{SPAWNER_SUBDOMAIN}.{BASE_DOMAIN}"
    )

    # ========================================
    # Magic Link Passwordless Auth
    # ========================================
    MAGIC_LINK_TOKEN_EXPIRY = int(os.getenv('MAGIC_LINK_TOKEN_EXPIRY', 900))  # 15 minutes
    MAGIC_LINK_RATE_LIMIT = int(os.getenv('MAGIC_LINK_RATE_LIMIT', 3))  # Max 3 per hour

    # ========================================
    # Debug & Administration
    # ========================================
    DEBUG_TOKEN = os.getenv('DEBUG_TOKEN') or None  # For admin debug API


class DevelopmentConfig(Config):
    """Entwicklungskonfiguration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Produktionskonfiguration."""
    DEBUG = False
    TESTING = False

    # Strict session security
    SESSION_COOKIE_SECURE = True

    # Optional: PostgreSQL instead of SQLite
    # SQLALCHEMY_DATABASE_URI = os.getenv(
    #     'DATABASE_URL',
    #     'postgresql://spawner:password@postgres:5432/spawner'
    # )


class TestingConfig(Config):
    """Testkonfiguration (In-Memory-Datenbank)."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Templates nach Klassendefinition initialisieren
Config.init_templates()


# Konfigurations-Dict für einfaches Laden
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
