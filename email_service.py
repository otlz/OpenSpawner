"""
Email-Service fuer Verifizierungs-Emails und Magic Links
"""
import smtplib
import secrets
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from datetime import datetime, timedelta


def generate_verification_token():
    """Generiert einen sicheren Verifizierungs-Token"""
    return secrets.token_urlsafe(32)


def generate_slug_from_email(email: str) -> str:
    """
    Generiert eindeutigen Slug aus Email
    Format: Erste 12 Zeichen von SHA256(email)
    """
    email_lower = email.lower().strip()
    hash_obj = hashlib.sha256(email_lower.encode())
    slug = hash_obj.hexdigest()[:12]
    return slug


def generate_magic_link_token() -> str:
    """
    Generiert sicheren Token für Magic Links
    32 Byte = ~43 Zeichen URL-safe Base64
    """
    return secrets.token_urlsafe(32)


def check_rate_limit(email: str) -> bool:
    """
    Prüft ob User zu viele Magic Links angefordert hat
    Max. 3 Tokens pro Email in den letzten 60 Minuten

    Returns:
        True wenn OK, False wenn Rate Limit erreicht
    """
    from models import User, MagicLinkToken

    user = User.query.filter_by(email=email).first()
    if not user:
        return True  # Neue Email, kein Limit

    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_tokens = MagicLinkToken.query.filter(
        MagicLinkToken.user_id == user.id,
        MagicLinkToken.created_at >= one_hour_ago
    ).count()

    return recent_tokens < 3


def send_magic_link_email(email: str, token: str, token_type: str) -> bool:
    """
    Sendet Magic Link Email

    Args:
        email: Empfänger-Email
        token: Magic Link Token
        token_type: 'signup' oder 'login'

    Returns:
        True bei Erfolg, False bei Fehler
    """
    # URL basierend auf Type
    if token_type == 'signup':
        verify_url = f"{Config.FRONTEND_URL}/verify-signup?token={token}"
        subject = "Registrierung abschließen - Container Spawner"
        action_text = "Registrierung abschließen"
        greeting = "Vielen Dank für deine Registrierung!"
    else:  # login
        verify_url = f"{Config.FRONTEND_URL}/verify-login?token={token}"
        subject = "Login-Link - Container Spawner"
        action_text = "Jetzt einloggen"
        greeting = "Hier ist dein Login-Link:"

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
                <h1>Container Spawner</h1>
            </div>
            <div class="content">
                <p>{greeting}</p>
                <p>Klicke auf den Button, um fortzufahren:</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="button">{action_text}</a>
                </p>
                <p>Oder kopiere diesen Link in deinen Browser:</p>
                <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">
                    {verify_url}
                </p>
                <p><small>Dieser Link ist 15 Minuten gültig und kann nur einmal verwendet werden.</small></p>
            </div>
            <div class="footer">
                <p>Diese Email wurde automatisch generiert. Bitte antworte nicht darauf.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    {greeting}

    Bitte öffne folgenden Link oder kopiere ihn in deinen Browser:

    {verify_url}

    Hinweis: Dieser Link ist 15 Minuten gültig und kann nur einmal verwendet werden.

    ---
    Diese Email wurde automatisch generiert.
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_FROM
    msg['To'] = email

    part1 = MIMEText(text_content, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

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

        print(f"[EMAIL] Magic Link ({token_type}) gesendet an {email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Fehler beim Senden der Email an {email}: {str(e)}")
        return False
