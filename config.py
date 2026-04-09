import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ========================================
    # Security
    # ========================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # JWT configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_TOKEN_LOCATION = ['headers']
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
    # Docker Configuration - Dynamic Template System
    # ========================================
    DOCKER_SOCKET = os.getenv('DOCKER_SOCKET', 'unix://var/run/docker.sock')

    # LEGACY: Still used by old spawn_container()
    USER_TEMPLATE_IMAGE = os.getenv('USER_TEMPLATE_IMAGE', 'user-template-01:latest')

    # ========================================
    # Dynamic Template Loading
    # ========================================

    @staticmethod
    def _extract_type_from_image(image_name: str) -> str:
        """
        Extract container type from image name.

        Examples:
            'user-template-01:latest' -> 'template-01'
            'user-template-next:latest' -> 'template-next'
            'custom-nginx:v1.0' -> 'custom-nginx'
        """
        # Remove tag (:latest, :v1.0, etc.)
        base_name = image_name.split(':')[0]

        # Remove 'user-' prefix if present
        if base_name.startswith('user-'):
            base_name = base_name[5:]  # 'user-template-01' -> 'template-01'

        return base_name

    @staticmethod
    def _load_template_images() -> list:
        """Load template image list from USER_TEMPLATE_IMAGES (semicolon-separated)"""
        raw_images = os.getenv('USER_TEMPLATE_IMAGES', '')
        if not raw_images:
            # Fallback for compatibility
            return ['user-template-01:latest']

        return [img.strip() for img in raw_images.split(';') if img.strip()]

    @staticmethod
    def _load_templates_config() -> dict:
        """Load template configuration from templates.json"""
        config_path = Path(__file__).parent / 'templates.json'

        if not config_path.exists():
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert array to dictionary (key=type)
            return {
                template['type']: template
                for template in data.get('templates', [])
            }
        except (json.JSONDecodeError, KeyError) as e:
            import sys
            print(f"[CONFIG] Warning: Error loading templates.json: {e}", file=sys.stderr)
            return {}

    # Temporary variables for template loading (processed after class definition)
    TEMPLATE_IMAGES = None
    TEMPLATES_CONFIG = None
    CONTAINER_TEMPLATES = None

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

    # Container cleanup
    CONTAINER_IDLE_TIMEOUT = int(os.getenv('CONTAINER_IDLE_TIMEOUT', 3600))  # 1h in seconds

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
    DEBUG_TOKEN = os.getenv('DEBUG_TOKEN', '')  # For admin debug API


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
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
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Initialize templates AFTER class definition
Config.TEMPLATE_IMAGES = Config._load_template_images()
Config.TEMPLATES_CONFIG = Config._load_templates_config()

# Build CONTAINER_TEMPLATES from templates
templates = {}
for image in Config.TEMPLATE_IMAGES:
    container_type = Config._extract_type_from_image(image)
    config_meta = Config.TEMPLATES_CONFIG.get(container_type, {})
    templates[container_type] = {
        'image': image,
        'display_name': config_meta.get('display_name', container_type.replace('-', ' ').title()),
        'description': config_meta.get('description', f'Container based on {image}')
    }
Config.CONTAINER_TEMPLATES = templates


# Config dict for easy loading
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
