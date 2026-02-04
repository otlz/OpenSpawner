#!/usr/bin/env python3
"""
Migration Script: Container Blocking Fields hinzufügen

Fügt folgende Spalten zur user_container Tabelle hinzu:
- is_blocked (BOOLEAN DEFAULT 0)
- blocked_at (DATETIME)
- blocked_by (INTEGER, Foreign Key zu user.id)

Verwendung:
  python migrate_container_blocking.py

Fallback (SQLite):
  sqlite3 spawner.db < migration.sql
"""

from app import app, db
import sys

def migrate():
    """Führt die Migration durch"""
    try:
        with app.app_context():
            print("[MIGRATION] Starte Container Blocking Migration...")

            # Prüfe ob Spalten bereits existieren
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user_container')]

            if 'is_blocked' in columns:
                print("[INFO] Spalte 'is_blocked' existiert bereits")
            else:
                print("[ADD] Füge Spalte 'is_blocked' hinzu...")
                with db.engine.connect() as conn:
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE user_container
                            ADD COLUMN is_blocked BOOLEAN DEFAULT 0 NOT NULL
                        """))
                        conn.commit()
                        print("✅ Spalte 'is_blocked' erstellt")
                    except Exception as e:
                        print(f"⚠️ Fehler bei 'is_blocked': {e}")
                        # Könnte bereits existieren (MySQL)

            if 'blocked_at' in columns:
                print("[INFO] Spalte 'blocked_at' existiert bereits")
            else:
                print("[ADD] Füge Spalte 'blocked_at' hinzu...")
                with db.engine.connect() as conn:
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE user_container
                            ADD COLUMN blocked_at DATETIME
                        """))
                        conn.commit()
                        print("✅ Spalte 'blocked_at' erstellt")
                    except Exception as e:
                        print(f"⚠️ Fehler bei 'blocked_at': {e}")

            if 'blocked_by' in columns:
                print("[INFO] Spalte 'blocked_by' existiert bereits")
            else:
                print("[ADD] Füge Spalte 'blocked_by' hinzu...")
                with db.engine.connect() as conn:
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE user_container
                            ADD COLUMN blocked_by INTEGER
                            REFERENCES user(id) ON DELETE SET NULL
                        """))
                        conn.commit()
                        print("✅ Spalte 'blocked_by' erstellt")
                    except Exception as e:
                        print(f"⚠️ Fehler bei 'blocked_by': {e}")

            print("\n[SUCCESS] Migration abgeschlossen!")
            print("[INFO] Folgende Änderungen wurden durchgeführt:")
            print("  - is_blocked BOOLEAN DEFAULT 0")
            print("  - blocked_at DATETIME")
            print("  - blocked_by INTEGER FK zu user(id)")
            print("\n[NEXT] Starte die Application mit: docker-compose up -d")

            return True

    except Exception as e:
        print(f"\n[ERROR] Migration fehlgeschlagen: {str(e)}")
        print("[HELP] Versuche manuelle Migration:")
        print("  sqlite3 spawner.db")
        print("  > ALTER TABLE user_container ADD COLUMN is_blocked BOOLEAN DEFAULT 0;")
        print("  > ALTER TABLE user_container ADD COLUMN blocked_at DATETIME;")
        print("  > ALTER TABLE user_container ADD COLUMN blocked_by INTEGER;")
        return False

if __name__ == '__main__':
    success = migrate()
    sys.exit(0 if success else 1)
