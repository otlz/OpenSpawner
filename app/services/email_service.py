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
        subject = "Registrierung abschließen · OpenSpawner"
        action_text = "Registrierung abschließen"
        heading = "Registrierung abschließen"
        intro = (
            "Danke für deine Registrierung. Bestätige deine E-Mail-Adresse, "
            "um deine persönliche Container-Umgebung zu aktivieren."
        )
        preheader = "Bestätige deine E-Mail-Adresse für OpenSpawner."
    else:  # login
        verify_url = f"{frontend_url}/verify-login?token={token}"
        subject = "Dein Anmeldelink · OpenSpawner"
        action_text = "Jetzt anmelden"
        heading = "Anmelden bei OpenSpawner"
        intro = "Mit einem Klick bist du angemeldet, ganz ohne Passwort."
        preheader = "Dein Anmeldelink für OpenSpawner."

    expiry_minutes = max(1, Config.MAGIC_LINK_TOKEN_EXPIRY // 60)

    # Styling matches the landing page (shadcn neutral palette): white card on
    # neutral-50, near-black primary button, muted grays. All styles inline,
    # table layout for email client compatibility.
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
    mono = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#fafafa;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">{preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#fafafa;">
  <tr>
    <td align="center" style="padding:48px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:440px;">
        <tr>
          <td style="padding:0 4px 16px;font-family:{font};font-size:16px;font-weight:600;letter-spacing:-0.2px;color:#0a0a0a;">
            OpenSpawner
          </td>
        </tr>
        <tr>
          <td style="background-color:#ffffff;border:1px solid #e5e5e5;border-radius:12px;padding:32px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="font-family:{font};font-size:20px;font-weight:600;letter-spacing:-0.3px;color:#0a0a0a;padding-bottom:8px;">
                  {heading}
                </td>
              </tr>
              <tr>
                <td style="font-family:{font};font-size:14px;line-height:22px;color:#737373;padding-bottom:24px;">
                  {intro}
                </td>
              </tr>
              <tr>
                <td>
                  <a href="{verify_url}" style="display:inline-block;background-color:#171717;color:#fafafa;font-family:{font};font-size:14px;font-weight:500;text-decoration:none;border-radius:10px;padding:11px 20px;">
                    {action_text}
                  </a>
                </td>
              </tr>
              <tr>
                <td style="font-family:{font};font-size:13px;line-height:20px;color:#737373;padding-top:28px;padding-bottom:8px;">
                  Oder kopiere diesen Link in deinen Browser:
                </td>
              </tr>
              <tr>
                <td>
                  <div style="background-color:#f5f5f5;border-radius:8px;padding:10px 12px;font-family:{mono};font-size:12px;line-height:18px;color:#525252;word-break:break-all;">
                    {verify_url}
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 4px 0;font-family:{font};font-size:12px;line-height:18px;color:#a3a3a3;">
            Der Link ist {expiry_minutes} Minuten gültig und kann nur einmal verwendet werden.<br>
            Diese E-Mail wurde automatisch erstellt, bitte antworte nicht darauf.
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
"""

    text_content = f"""{heading}

{intro}

Öffne den folgenden Link oder kopiere ihn in deinen Browser:

{verify_url}

Hinweis: Der Link ist {expiry_minutes} Minuten gültig und kann nur einmal verwendet werden.

---
Diese E-Mail wurde automatisch erstellt, bitte antworte nicht darauf.
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
