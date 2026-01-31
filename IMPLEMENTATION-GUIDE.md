# Passwordless Authentication - Implementierungsanleitung

## ✅ Was wurde implementiert

Das Container Spawner System wurde komplett auf **Passwordless Authentication mit Magic Links** umgestellt.

### Backend-Änderungen (Python/Flask)

#### 1. **Datenbank-Schema** (`models.py`)
- ❌ Entfernt: `username` Spalte
- ❌ Entfernt: `password_hash` Spalte
- ✅ Hinzugefügt: `slug` Spalte (unique, 12 Zeichen, basierend auf Email-Hash)
- ✅ Neue Tabelle: `MagicLinkToken` für Magic Link Tokens
  - `token` - der Magic Link Token (unique)
  - `token_type` - 'signup' oder 'login'
  - `expires_at` - Ablaufzeit (15 Minuten)
  - `used_at` - Zeitstempel wenn Token verwendet wurde
  - `is_valid()` - Methode zur Validierung
  - `mark_as_used()` - Methode zum Markieren als verwendet

#### 2. **Email-Service** (`email_service.py`)
- ✅ `generate_slug_from_email(email)` - Generiert eindeutigen Slug aus Email
- ✅ `generate_magic_link_token()` - Generiert sicheren Token
- ✅ `send_magic_link_email(email, token, token_type)` - Sendet Magic Link per Email
- ✅ `check_rate_limit(email)` - Rate-Limiting (max 3 Tokens/Stunde)

#### 3. **API Routes** (`api.py`)
- ✅ `POST /api/auth/login` - Sendet Magic Link statt Passwort zu prüfen
- ✅ `POST /api/auth/signup` - Sendet Magic Link für Registrierung
- ✅ `GET /api/auth/verify-signup` - Verifiziert Signup Token & erstellt JWT
- ✅ `GET /api/auth/verify-login` - Verifiziert Login Token & erstellt JWT
- ❌ Gelöscht: `/api/auth/verify` (alte Email-Verifizierung)
- ❌ Gelöscht: `/api/auth/resend-verification`
- ✅ Angepasst: `/api/user/me` - Nutzt `slug` statt `username`
- ✅ Angepasst: `/api/container/restart` - Nutzt `slug`

#### 4. **Admin API** (`admin_api.py`)
- ❌ Gelöscht: `/api/admin/users/{id}/reset-password`
- ✅ Angepasst: `resend_verification()` - Sendet Magic Link statt Password-Reset
- ✅ Alle `user.username` Referenzen → `user.email`

#### 5. **Container Manager** (`container_manager.py`)
- ✅ `spawn_container(user_id, slug)` - Nutzt `slug` statt `username`
- ✅ Traefik-Labels aktualisiert: `/username` → `/slug`
- ✅ Environment: `USERNAME` → `USER_SLUG`
- ✅ `start_container()` - Neue Methode zum Starten gestoppter Container
- ✅ `_get_user_container()` - Nutzt `slug` statt `username`

#### 6. **Konfiguration** (`config.py`)
- ✅ `MAGIC_LINK_TOKEN_EXPIRY = 900` (15 Minuten)
- ✅ `MAGIC_LINK_RATE_LIMIT = 3` (3 Tokens pro Stunde)

### Frontend-Änderungen (TypeScript/React)

#### 1. **API Client** (`src/lib/api.ts`)
- ✅ Neue `User` Interface: `email`, `slug`, `state`, keine `username`
- ✅ `api.auth.login(email)` - nur Email statt username+password
- ✅ `api.auth.signup(email)` - nur Email
- ✅ `api.auth.verifySignup(token)` - Verifiziert Signup Token
- ✅ `api.auth.verifyLogin(token)` - Verifiziert Login Token
- ✅ QueryParams Support in `fetchApi()`

#### 2. **Auth Hook** (`src/hooks/use-auth.tsx`)
- ✅ `login(email)` - Magic Link Request
- ✅ `signup(email)` - Magic Link Request
- ✅ `verifySignup(token)` - Token-Verifizierung
- ✅ `verifyLogin(token)` - Token-Verifizierung
- ✅ State Management: Error Tracking, isAuthenticated

#### 3. **Login Page** (`src/app/login/page.tsx`)
- ✅ Email-Input statt Username+Password
- ✅ "Email gesendet" Nachricht nach Submit
- ✅ Option, neue Email anzufordern

#### 4. **Signup Page** (`src/app/signup/page.tsx`)
- ✅ Email-Input nur (kein Username/Password mehr)
- ✅ "Email gesendet" Nachricht nach Submit
- ✅ Link zu Login

#### 5. **Neue Pages**
- ✅ `src/app/verify-signup/page.tsx` - Signup-Token Verifizierung
  - Token aus URL auslesen
  - API aufrufen
  - JWT speichern
  - Zu Dashboard umleiten
- ✅ `src/app/verify-login/page.tsx` - Login-Token Verifizierung
  - Token aus URL auslesen
  - API aufrufen
  - JWT speichern
  - Zu Dashboard umleiten

#### 6. **Dashboard** (`src/app/dashboard/page.tsx`)
- ✅ Container Slug anzeigen
- ✅ Email statt Username in Header
- ✅ Service-URL nutzt Slug

## 🚀 Erste Schritte nach Deployment

### 1. SMTP konfigurieren
Stelle sicher, dass deine `.env` folgendes enthält:
```
SMTP_HOST=dein-smtp-server.com
SMTP_PORT=587
SMTP_USER=deine-email@domain.com
SMTP_PASSWORD=dein-app-passwort
SMTP_FROM=noreply@domain.com
FRONTEND_URL=https://coder.deine-domain.com
```

**Datenbank:** Wird automatisch beim Start erstellt (alle Tabellen inkl. MagicLinkToken)

### 2. Magic Link Einstellungen anpassen (optional)
```env
# Token Gültigkeitsdauer in Sekunden (Standard: 900 = 15 Minuten)
MAGIC_LINK_TOKEN_EXPIRY=900

# Rate-Limiting: Max Tokens pro Stunde (Standard: 3)
MAGIC_LINK_RATE_LIMIT=3
```

## 📧 User Journey

### Registrierung
1. User klickt auf "Registrierung"
2. Gibt Email ein
3. Backend sendet Magic Link per Email (Gültig 15 Minuten)
4. User klickt Link → Token wird verifiziert
5. Account wird erstellt & Container spawnt
6. JWT wird gespeichert
7. Auto-Redirect zu Dashboard

### Login
1. User klickt auf "Login"
2. Gibt Email ein
3. Backend sendet Magic Link per Email
4. User klickt Link → Token wird verifiziert
5. JWT wird gespeichert
6. Auto-Redirect zu Dashboard

## 🔗 Container URLs

**Alt (deprecated):**
```
https://coder.domain.com/username
```

**Neu (mit Slug):**
```
https://coder.domain.com/u-a3f9c2d1  # Beispiel: erste 12 Zeichen von SHA256(email)
```

Der Slug ist eindeutig und kann im Dashboard angesehen werden.

## 🔒 Security Features

- **One-Time Use Tokens** - Magic Link kann nur einmal verwendet werden
- **Token Expiration** - Tokens verfallen nach 15 Minuten
- **Rate Limiting** - Max 3 Token-Anfragen pro Email pro Stunde
- **User Enumeration Protection** - Gleiche Meldung ob Email registriert oder nicht
- **Container Isolation** - User-Container haben keinen Zugriff auf Docker Socket
- **No Passwords** - Keine Passwort-Speicherung, kein Passwort-Reset möglich

## 📝 Wichtige Änderungen im Überblick

| Bereich | Alt | Neu |
|---------|-----|-----|
| **Login Feld** | Username + Password | Email nur |
| **Signup Felder** | Username + Email + Password | Email nur |
| **Container ID** | user-{username}-{id} | user-{slug}-{id} |
| **Container URL** | /username | /{slug} |
| **User Identifier** | Username | Email |
| **Authentifizierung** | Username/Password | Magic Link (Email) |
| **Auth-Endpunkte** | /verify | /verify-signup, /verify-login |

## 🐛 Troubleshooting

### "Email konnte nicht gesendet werden"
- Überprüfe SMTP-Konfiguration in `.env`
- Teste: `docker logs spawner` → SMTP Fehler?
- Sind alle SMTP-Credentials korrekt?

### "Token ist abgelaufen"
- Standard-Expiration: 15 Minuten
- Kann in `.env` angepasst werden: `MAGIC_LINK_TOKEN_EXPIRY=900`

### Rate-Limiting blockiert
- Max 3 Requests pro Email pro Stunde
- Warte 1 Stunde oder ändere in `.env`: `MAGIC_LINK_RATE_LIMIT=5`

### Container spawnt nicht
- `docker logs spawner` überprüfen
- Container Template Image existiert? `docker images | grep user-template`
- Traefik Network konfiguriert?

## 📚 Weitere Ressourcen

- **CLAUDE.md** - Projekt-Übersicht und Architektur
- **Backend Logs** - `docker logs spawner`
- **Frontend Logs** - Browser Console (F12)
- **Container Logs** - `docker logs user-{slug}-{id}`

## ✨ Nächste Phase (optional)

1. **Admin Magic Link** - Admins können Benutzern Magic Links senden
2. **Two-Factor Auth** - Optional 2FA mit TOTP
3. **WebAuthn** - Biometric/FIDO2 support
4. **Session Management** - Token-Refresh, Logout überall

---

**Implementiert von:** Claude Code
**Datum:** 2026-01-31
**Version:** 1.0.0 (Passwordless Auth)
