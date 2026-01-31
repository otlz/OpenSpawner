"""
Email-Service fuer Verifizierungs-Emails
"""
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def generate_verification_token():
    """Generiert einen sicheren Verifizierungs-Token"""
    return secrets.token_urlsafe(32)


def send_verification_email(user_email, username, token, base_url=None):
    """
    Sendet eine Verifizierungs-Email an den Benutzer.

    Args:
        user_email: Email-Adresse des Benutzers
        username: Benutzername
        token: Verifizierungs-Token
        base_url: Basis-URL fuer den Verifizierungs-Link (optional)

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if base_url is None:
        base_url = Config.FRONTEND_URL

    verify_url = f"{base_url}/verify-success?token={token}"

    # Email-Inhalt
    subject = "Bestatige deine Email-Adresse - Container Spawner"

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
                <h2>Hallo {username}!</h2>
                <p>Vielen Dank fuer deine Registrierung beim Container Spawner.</p>
                <p>Bitte bestatige deine Email-Adresse, indem du auf den folgenden Button klickst:</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="button">Email bestaetigen</a>
                </p>
                <p>Oder kopiere diesen Link in deinen Browser:</p>
                <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 3px;">
                    {verify_url}
                </p>
                <p><strong>Hinweis:</strong> Dieser Link ist nur einmal verwendbar.</p>
            </div>
            <div class="footer">
                <p>Diese Email wurde automatisch generiert. Bitte antworte nicht darauf.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Hallo {username}!

    Vielen Dank fuer deine Registrierung beim Container Spawner.

    Bitte bestatige deine Email-Adresse, indem du folgenden Link oeffnest:

    {verify_url}

    Hinweis: Dieser Link ist nur einmal verwendbar.

    ---
    Diese Email wurde automatisch generiert.
    """

    # Email erstellen
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_FROM
    msg['To'] = user_email

    # Text- und HTML-Teil hinzufuegen
    part1 = MIMEText(text_content, 'plain', 'utf-8')
    part2 = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    try:
        # SMTP-Verbindung
        if Config.SMTP_USE_TLS:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT)

        # Authentifizierung wenn konfiguriert
        if Config.SMTP_USER and Config.SMTP_PASSWORD:
            server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)

        # Email senden
        server.sendmail(Config.SMTP_FROM, user_email, msg.as_string())
        server.quit()

        print(f"[EMAIL] Verifizierungs-Email gesendet an {user_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Fehler beim Senden der Email an {user_email}: {str(e)}")
        return False


def send_password_reset_email(user_email, username, new_password):
    """
    Sendet eine Email mit dem neuen Passwort an den Benutzer.

    Args:
        user_email: Email-Adresse des Benutzers
        username: Benutzername
        new_password: Das neue Passwort

    Returns:
        True bei Erfolg, False bei Fehler
    """
    subject = "Dein Passwort wurde zurueckgesetzt - Container Spawner"

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
            .password {{ background: #eee; padding: 15px; font-family: monospace; font-size: 18px; text-align: center; border-radius: 5px; }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Container Spawner</h1>
            </div>
            <div class="content">
                <h2>Hallo {username}!</h2>
                <p>Ein Administrator hat dein Passwort zurueckgesetzt.</p>
                <p>Dein neues Passwort lautet:</p>
                <p class="password">{new_password}</p>
                <p><strong>Wichtig:</strong> Bitte aendere dieses Passwort nach dem ersten Login!</p>
            </div>
            <div class="footer">
                <p>Diese Email wurde automatisch generiert. Bitte antworte nicht darauf.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Hallo {username}!

    Ein Administrator hat dein Passwort zurueckgesetzt.

    Dein neues Passwort lautet: {new_password}

    Wichtig: Bitte aendere dieses Passwort nach dem ersten Login!

    ---
    Diese Email wurde automatisch generiert.
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.SMTP_FROM
    msg['To'] = user_email

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

        server.sendmail(Config.SMTP_FROM, user_email, msg.as_string())
        server.quit()

        print(f"[EMAIL] Passwort-Reset-Email gesendet an {user_email}")
        return True

    except Exception as e:
        print(f"[EMAIL] Fehler beim Senden der Email an {user_email}: {str(e)}")
        return False
