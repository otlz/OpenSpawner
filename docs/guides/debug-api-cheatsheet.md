# DEBUG-API Quick Reference (Cheatsheet)

## 🚀 Schnelle Befehle

### Swagger UI öffnen
```bash
http://localhost:5000/swagger
```

### View Logs
```bash
curl -H "X-Debug-Token: SECRET" \
  "http://localhost:5000/api/admin/debug?action=view-logs" | jq '.logs'
```

### List Users
```bash
curl -H "X-Debug-Token: SECRET" \
  "http://localhost:5000/api/admin/debug?action=list-users" | jq '.users'
```

### Delete User (⚠️ Warning!)
```bash
curl -H "X-Debug-Token: SECRET" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=test@example.com"
```

### Delete Tokens
```bash
curl -H "X-Debug-Token: SECRET" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=spam@example.com"
```

### Clear Logs
```bash
curl -H "X-Debug-Token: SECRET" \
  "http://localhost:5000/api/admin/debug?action=clear-logs"
```

---

## 🔐 Authentifizierung

### Methode 1: DEBUG_TOKEN
```bash
curl -H "X-Debug-Token: your-secret-token" \
  "http://localhost:5000/api/admin/debug?action=list-users"
```

### Methode 2: JWT Token
```bash
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=list-users"
```

---

## 📋 Alle Actions

| Action | Methode | Parameter | Beschreibung |
|--------|---------|-----------|--------------|
| `view-logs` | GET | - | Zeigt letzte 100 Log-Zeilen |
| `clear-logs` | GET/POST | - | Löscht alle Logs |
| `list-users` | GET | - | Listet alle User auf |
| `delete-email` | GET/POST | `email=...` | Löscht User + Daten |
| `delete-token` | GET/POST | `email=...` | Löscht Tokens für User |
| `info` | GET | - | Zeigt diese Hilfe |

---

## 🎯 Häufige Use-Cases

### Use-Case 1: User hat zu viele Magic Links (Spam)
```bash
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=delete-token&email=user@example.com"
```

### Use-Case 2: User-Container ist kaputt, User löschen + neu starten
```bash
# 1. Alten User löschen
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=delete-email&email=user@example.com"

# 2. User kann sich neu registrieren
```

### Use-Case 3: Logs einmal wöchentlich leeren
```bash
# Cronjob
0 0 * * 0 curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=clear-logs"
```

### Use-Case 4: Alle User sehen
```bash
curl -H "X-Debug-Token: $DEBUG_TOKEN" \
  "http://localhost:5000/api/admin/debug?action=list-users" | \
  jq -r '.users[] | "\(.email) (\(.state))"'

# Output:
# admin@example.com (active)
# user1@example.com (verified)
# user2@example.com (registered)
```

---

## ⚡ Pro-Tipps

### Shell Alias für schnellere Befehle
```bash
# In ~/.bashrc oder ~/.zshrc hinzufügen:
alias spawner-logs='curl -H "X-Debug-Token: $DEBUG_TOKEN" "http://localhost:5000/api/admin/debug?action=view-logs" | jq'
alias spawner-users='curl -H "X-Debug-Token: $DEBUG_TOKEN" "http://localhost:5000/api/admin/debug?action=list-users" | jq'
```

### Dann nutzen:
```bash
spawner-logs     # Zeigt Logs
spawner-users    # Zeigt User
```

### JSON Output formatieren
```bash
# Pretty-print
curl ... | jq '.'

# Nur spezifische Felder
curl ... | jq '.users[] | {email, state, created_at}'

# Filter
curl ... | jq '.users[] | select(.is_blocked == true)'
```

### Logs in Echtzeit verfolgen
```bash
docker-compose logs -f spawner | grep -i "error\|warning"
```

---

## 🔒 Sicherheits-Checkliste

- [ ] DEBUG_TOKEN ist mindestens 32 Zeichen lang
- [ ] DEBUG_TOKEN ist in `.env` und NICHT im Git
- [ ] DEBUG-API nur intern/localhost erreichbar (nicht exponiert)
- [ ] Regelmäßig Logs leeren (Privacy)
- [ ] User-Löschungen werden geloggt
- [ ] Nur Admins haben Zugriff auf DEBUG_TOKEN

---

## 🆘 Schnelle Hilfe

**Swagger zeigt 404?**
```bash
docker-compose restart spawner
docker exec spawner pip install flasgger==0.9.7.1
```

**DEBUG_TOKEN funktioniert nicht?**
```bash
# Prüfe ob gesetzt
docker exec spawner cat /app/.env | grep DEBUG_TOKEN

# Falls leer, neu setzen
docker-compose down
nano .env  # DEBUG_TOKEN hinzufügen
docker-compose up -d
```

**Kann User nicht löschen?**
```bash
# Prüfe Logs
docker-compose logs spawner | grep -i "error"

# User manuell prüfen
docker exec spawner python3 -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    print(user)
"
```

---

**Stand:** 2026-02-02
**Flasgger:** 0.9.7.1
**OpenAPI:** 3.0.0
