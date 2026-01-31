from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum


db = SQLAlchemy()


class UserState(Enum):
    """Benutzer-Status fuer Email-Verifizierung und Aktivitaet"""
    REGISTERED = 'registered'   # Signup abgeschlossen, Email nicht verifiziert
    VERIFIED = 'verified'       # Email verifiziert, Container noch nie genutzt
    ACTIVE = 'active'           # Container mindestens einmal gestartet


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    container_id = db.Column(db.String(100), nullable=True)
    container_port = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Admin-Felder
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Sperr-Felder
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Email-Verifizierung und Status
    state = db.Column(db.String(20), default=UserState.REGISTERED.value, nullable=False)
    verification_token = db.Column(db.String(64), nullable=True)
    verification_sent_at = db.Column(db.DateTime, nullable=True)

    # Aktivitaetstracking
    last_used = db.Column(db.DateTime, nullable=True)

    # Beziehung fuer blocked_by
    blocker = db.relationship('User', remote_side=[id], foreign_keys=[blocked_by])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Konvertiert User zu Dictionary fuer API-Responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'state': self.state,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'container_id': self.container_id
        }


class AdminTakeoverSession(db.Model):
    """Protokolliert Admin-Zugriffe auf User-Container (Phase 2)"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(500), nullable=True)

    admin = db.relationship('User', foreign_keys=[admin_id])
    target_user = db.relationship('User', foreign_keys=[target_user_id])