"""
Persönliches Wörterbuch - Flask Backend mit SQLite
Speichert Wörter und Bedeutungen in einer persistenten Datenbank pro Benutzer
"""

from flask import Flask, render_template, request, jsonify, g
from datetime import datetime
import sqlite3
import os
import logging
import jwt

app = Flask(__name__)

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pfad zur persistenten Datenbank (wird als Docker Volume gemountet)
DB_PATH = "/data/app.db"
os.makedirs("/data", exist_ok=True)

logger.info(f"[DICTIONARY] Database path: {DB_PATH}")


def get_db():
    """Verbindung zur SQLite-Datenbank"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Erstelle Tabelle beim Start (falls noch nicht vorhanden)"""
    conn = get_db()
    cursor = conn.cursor()

    # Prüfe ob Tabelle bereits existiert
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='words'
    """)

    if not cursor.fetchone():
        logger.info("[DICTIONARY] Creating 'words' table...")
        cursor.execute('''
            CREATE TABLE words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                meaning TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("[DICTIONARY] Table 'words' created successfully")
    else:
        logger.info("[DICTIONARY] Table 'words' already exists")

    conn.close()


# ============================================================
# JWT-Token Validierung
# ============================================================
JWT_SECRET = os.getenv('JWT_SECRET', 'secret-key-from-spawner')  # Sollte vom Spawner gesetzt werden

def validate_jwt_token():
    """Validiere JWT-Token aus Cookie - wird vor jedem Request ausgeführt"""
    # GET / ist öffentlich (index.html laden)
    if request.path == '/' and request.method == 'GET':
        return

    # GET /health ist öffentlich (Health Check)
    if request.path == '/health' and request.method == 'GET':
        return

    # Alle anderen Endpoints brauchen gültigen JWT-Token im Cookie
    token = request.cookies.get('spawner_token')

    if not token:
        return jsonify({'error': 'Authentifizierung erforderlich - kein Token'}), 401

    try:
        # Dekodiere und validiere JWT
        # Hinweis: Der Secret-Key muss mit dem Spawner synchron sein!
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        # Speichere User-ID im g-Object für API-Endpunkte
        g.user_id = payload.get('sub')  # 'sub' ist die Standard-Claim für User-ID
        logger.info(f"[DICTIONARY] Token validiert für User {g.user_id}")
    except jwt.ExpiredSignatureError:
        logger.warning("[DICTIONARY] JWT-Token abgelaufen")
        return jsonify({'error': 'Token abgelaufen - bitte neu anmelden'}), 401
    except jwt.InvalidTokenError as e:
        logger.warning(f"[DICTIONARY] Ungültiger JWT-Token: {str(e)}")
        return jsonify({'error': 'Ungültiger Token - authentifizieren erforderlich'}), 401
    except Exception as e:
        logger.error(f"[DICTIONARY] Token-Validierungsfehler: {str(e)}")
        return jsonify({'error': 'Authentifizierungsfehler'}), 500


# Registriere before_request Handler
app.before_request(validate_jwt_token)


@app.route('/')
def index():
    """Hauptseite mit HTML-Interface"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health Check Endpoint für Docker"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        logger.error(f"[DICTIONARY] Health check failed: {e}")
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/api/words', methods=['GET'])
def get_words():
    """Alle gespeicherten Wörter abrufen"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, word, meaning, created_at FROM words ORDER BY created_at DESC')
        words = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"[DICTIONARY] Retrieved {len(words)} words")
        return jsonify({
            'words': words,
            'count': len(words)
        }), 200
    except Exception as e:
        logger.error(f"[DICTIONARY] Error retrieving words: {e}")
        return jsonify({'error': 'Fehler beim Abrufen der Wörter'}), 500


@app.route('/api/words', methods=['POST'])
def add_word():
    """Neues Wort hinzufügen"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400

        word = data.get('word', '').strip()
        meaning = data.get('meaning', '').strip()

        # Validierung
        if not word or not meaning:
            return jsonify({'error': 'Wort und Bedeutung sind erforderlich'}), 400

        if len(word) > 255:
            return jsonify({'error': 'Wort ist zu lang (max. 255 Zeichen)'}), 400

        if len(meaning) > 2000:
            return jsonify({'error': 'Bedeutung ist zu lang (max. 2000 Zeichen)'}), 400

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'INSERT INTO words (word, meaning) VALUES (?, ?)',
                (word, meaning)
            )
            conn.commit()
            word_id = cursor.lastrowid

            # Neuen Eintrag zurück
            cursor.execute('SELECT id, word, meaning, created_at FROM words WHERE id = ?', (word_id,))
            new_word = dict(cursor.fetchone())
            conn.close()

            logger.info(f"[DICTIONARY] Word added: '{word}'")
            return jsonify(new_word), 201

        except sqlite3.IntegrityError:
            conn.close()
            logger.warning(f"[DICTIONARY] Duplicate word: '{word}'")
            return jsonify({'error': f'Das Wort "{word}" existiert bereits'}), 409

    except Exception as e:
        logger.error(f"[DICTIONARY] Error adding word: {e}")
        return jsonify({'error': 'Fehler beim Speichern des Wortes'}), 500


@app.route('/api/words/<int:word_id>', methods=['PUT'])
def update_word(word_id):
    """Wort aktualisieren"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Keine Daten empfangen'}), 400

        word = data.get('word', '').strip()
        meaning = data.get('meaning', '').strip()

        # Validierung
        if not word or not meaning:
            return jsonify({'error': 'Wort und Bedeutung sind erforderlich'}), 400

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'UPDATE words SET word = ?, meaning = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (word, meaning, word_id)
            )
            conn.commit()

            if cursor.rowcount == 0:
                conn.close()
                return jsonify({'error': 'Wort nicht gefunden'}), 404

            # Aktualisiertes Wort zurück
            cursor.execute('SELECT id, word, meaning, created_at FROM words WHERE id = ?', (word_id,))
            updated_word = dict(cursor.fetchone())
            conn.close()

            logger.info(f"[DICTIONARY] Word updated: ID {word_id}")
            return jsonify(updated_word), 200

        except sqlite3.IntegrityError:
            conn.close()
            logger.warning(f"[DICTIONARY] Duplicate word on update: '{word}'")
            return jsonify({'error': f'Das Wort "{word}" existiert bereits'}), 409

    except Exception as e:
        logger.error(f"[DICTIONARY] Error updating word: {e}")
        return jsonify({'error': 'Fehler beim Aktualisieren des Wortes'}), 500


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    """Wort löschen"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM words WHERE id = ?', (word_id,))
        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Wort nicht gefunden'}), 404

        conn.close()
        logger.info(f"[DICTIONARY] Word deleted: ID {word_id}")
        return '', 204

    except Exception as e:
        logger.error(f"[DICTIONARY] Error deleting word: {e}")
        return jsonify({'error': 'Fehler beim Löschen des Wortes'}), 500


@app.route('/api/stats')
def get_stats():
    """Statistiken über die Wörterbuch-Datenbank"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM words')
        total = cursor.fetchone()['total']

        cursor.execute('SELECT MAX(created_at) as last_added FROM words')
        last_added = cursor.fetchone()['last_added']

        conn.close()

        return jsonify({
            'total_words': total,
            'last_added': last_added,
            'database': 'sqlite3',
            'storage': '/data/app.db'
        }), 200

    except Exception as e:
        logger.error(f"[DICTIONARY] Error getting stats: {e}")
        return jsonify({'error': 'Fehler beim Abrufen der Statistiken'}), 500


@app.errorhandler(404)
def not_found(error):
    """404 Handler"""
    return jsonify({'error': 'Endpoint nicht gefunden'}), 404


@app.errorhandler(500)
def server_error(error):
    """500 Handler"""
    logger.error(f"[DICTIONARY] Server error: {error}")
    return jsonify({'error': 'Interner Fehler'}), 500


if __name__ == '__main__':
    logger.info("[DICTIONARY] Starting Flask application...")
    init_db()
    logger.info("[DICTIONARY] Database initialized")
    app.run(host='0.0.0.0', port=8080, debug=False)
