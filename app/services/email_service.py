"""E-Mail-Service für Verifizierungs-E-Mails und Magic-Links."""
import fnmatch
import logging
import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def generate_verification_token():
    """Erzeugt einen sicheren Verifizierungs-Token."""
    return secrets.token_urlsafe(32)


def generate_slug_from_email(email: str) -> str:
    """Erzeugt einen eindeutigen Slug aus der E-Mail (erste 12 Zeichen von SHA256)."""
    email_lower = email.lower().strip()
    hash_obj = hashlib.sha256(email_lower.encode())
    slug = hash_obj.hexdigest()[:12]
    return slug


def generate_magic_link_token() -> str:
    """Erzeugt einen sicheren Token für Magic-Links (32 Bytes URL-safe Base64)."""
    return secrets.token_urlsafe(32)


def check_rate_limit(email: str) -> bool:
    """Prüft ob das Rate-Limit erreicht ist (max. 3 Tokens pro Stunde). True = OK."""
    from app.models import User, MagicLinkToken

    user = User.query.filter_by(email=email).first()
    if not user:
        return True  # New email, no limit

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_tokens = MagicLinkToken.query.filter(
        MagicLinkToken.user_id == user.id,
        MagicLinkToken.created_at >= one_hour_ago
    ).count()

    return recent_tokens < 3


def check_email_allowed(email: str) -> tuple:
    """
    Prüft ob eine E-Mail-Adresse per Whitelist/Blacklist zugelassen ist.
    Gibt (allowed: bool, reason: str) zurück.

    Algorithmus:
    1. Keine Regeln → alle erlaubt (offene Registrierung)
    2. Whitelist hat Vorrang: Match → ERLAUBT
    3. Blacklist: Match → GESPERRT
    4. Kein Match → erlaubt (Standard: offen)
    """
    from app.models import EmailRule

    rules = EmailRule.query.all()
    if not rules:
        return True, ''

    whitelist = [r.pattern.lower() for r in rules if r.rule_type == 'whitelist']
    blacklist = [r.pattern.lower() for r in rules if r.rule_type == 'blacklist']

    email_lower = email.lower()

    # Whitelist hat Vorrang
    for pattern in whitelist:
        if fnmatch.fnmatch(email_lower, pattern):
            return True, ''

    # Blacklist prüfen
    for pattern in blacklist:
        if fnmatch.fnmatch(email_lower, pattern):
            return False, 'Diese E-Mail-Adresse ist nicht zugelassen'

    return True, ''


def send_magic_link_email(email: str, token: str, token_type: str) -> bool:
    """Sendet eine Magic-Link-E-Mail (signup oder login). True bei Erfolg."""
    # In local dev mode, use localhost:3000 for the frontend URL
    frontend_url = Config.FRONTEND_URL
    if Config.BASE_DOMAIN == 'localhost':
        frontend_url = 'http://localhost:3000'

    # URL based on type
    if token_type == 'signup':
        verify_url = f"{frontend_url}/verify-signup?token={token}"
        subject = "Complete Registration - OpenSpawner"
        action_text = "Complete Registration"
        greeting = "Thank you for registering!"
    else:  # login
        verify_url = f"{frontend_url}/verify-login?token={token}"
        subject = "Login Link - OpenSpawner"
        action_text = "Log In Now"
        greeting = "Here is your login link:"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #1a1a2e; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px; background: #f9f9f9; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #4f46e5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>OpenSpawner</h1>
            </div>
            <div class="content">
                <p>{greeting}</p>
                <p>Click the button below to continue:</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="button">{action_text}</a>
                </p>
                <p>Or copy this link into your browser:</p>
                <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">
                    {verify_url}
                </p>
                <p><small>This link is valid for 15 minutes and can only be used once.</small></p>
            </div>
            <div class="footer">
                <p>This email was generated automatically. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    {greeting}

    Please open the following link or copy it into your browser:

    {verify_url}

    Note: This link is valid for 15 minutes and can only be used once.

    ---
    This email was generated automatically.
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_FROM
    msg['To'] = email

    part1 = MIMEText(text_content, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    # In local dev mode (no SMTP configured), just log the URL
    if not Config.SMTP_USER or Config.BASE_DOMAIN == 'localhost':
        logger.info(f"[EMAIL] ========================================")
        logger.info(f"[EMAIL] MAGIC LINK for {email} ({token_type}):")
        logger.info(f"[EMAIL] {verify_url}")
        logger.info(f"[EMAIL] ========================================")
        return True

    try:
        if Config.SMTP_USE_TLS:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)

        if Config.SMTP_USER and Config.SMTP_PASSWORD:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)

        server.sendmail(Config.SMTP_FROM, email, msg.as_string())
        server.quit()

        logger.info(f"[EMAIL] Magic link ({token_type}) sent to {email}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL] Error sending email to {email}: {str(e)}")
        logger.info(f"[EMAIL] Fallback - use this link: {verify_url}")
        return False
