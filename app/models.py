"""SQLAlchemy-Modelle für Benutzer, Container, Tokens und Admin-Sessions."""
from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
from enum import Enum


class UserState(Enum):
    """Benutzerstatus für E-Mail-Verifizierung und Aktivität."""
    REGISTERED = 'registered'   # Signup completed, email not verified
    VERIFIED = 'verified'       # Email verified, container never used
    ACTIVE = 'active'           # Container started at least once


class UserRole(Enum):
    """Benutzerrollen für Zugriffskontrolle."""
    ADMIN = 'admin'       # App-Administrator (1-2 pro Schule)
    MANAGER = 'manager'   # Lehrer — kann Templates und Container verwalten
    USER = 'user'         # Schüler — kann Container starten


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(12), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Role-based access control
    role = db.Column(db.String(20), default=UserRole.USER.value, nullable=False)

    # Blocking fields
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Email verification and status
    state = db.Column(db.String(20), default=UserState.REGISTERED.value, nullable=False)

    # Activity tracking
    last_used = db.Column(db.DateTime, nullable=True)

    @property
    def is_admin(self):
        """Abwärtskompatibilität: Prüft ob der Benutzer Admin ist."""
        return self.role == UserRole.ADMIN.value

    # Relationship for blocked_by
    blocker = db.relationship('User', remote_side=[id], foreign_keys=[blocked_by])

    # Multi-container support (explicit primaryjoin due to multiple FKs to User)
    containers = db.relationship('UserContainer',
                                primaryjoin='User.id==UserContainer.user_id',
                                back_populates='user',
                                cascade='all, delete-orphan')

    @property
    def container_id(self):
        """Abwärtskompatibilität: Gibt die Primär-Container-ID zurück."""
        if self.containers:
            return self.containers[0].container_id
        return None

    @container_id.setter
    def container_id(self, value):
        """Abwärtskompatibilität: Setzt die Primär-Container-ID."""
        if not self.containers:
            # Create primary container if not present
            from config import Config
            primary = UserContainer(
                user_id=self.id,
                container_type='template-nginx',
                template_image=Config.USER_TEMPLATE_IMAGE
            )
            db.session.add(primary)
            db.session.flush()
            self.containers.append(primary)
        self.containers[0].container_id = value

    @property
    def container_port(self):
        """Abwärtskompatibilität: Gibt den Primär-Container-Port zurück."""
        if self.containers:
            return self.containers[0].container_port
        return None

    @container_port.setter
    def container_port(self, value):
        """Abwärtskompatibilität: Setzt den Primär-Container-Port."""
        if not self.containers:
            # Create primary container if not present
            from config import Config
            primary = UserContainer(
                user_id=self.id,
                container_type='template-nginx',
                template_image=Config.USER_TEMPLATE_IMAGE
            )
            db.session.add(primary)
            db.session.flush()
            self.containers.append(primary)
        self.containers[0].container_port = value

    def to_dict(self):
        """Konvertiert den Benutzer in ein Dictionary für API-Antworten."""
        return {
            'id': self.id,
            'email': self.email,
            'slug': self.slug,
            'role': self.role,
            'is_admin': self.is_admin,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'state': self.state,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'container_id': self.container_id
        }


class MagicLinkToken(db.Model):
    """Magic-Link-Tokens für passwortlose Authentifizierung."""
    __tablename__ = 'magic_link_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'signup' or 'login'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', backref=db.backref('magic_tokens', lazy=True, cascade='all, delete-orphan'))

    def is_valid(self):
        """Prüft ob der Token noch gültig ist (nicht verwendet und nicht abgelaufen)."""
        if self.used_at is not None:
            return False  # Token already used
        if datetime.utcnow() > self.expires_at:
            return False  # Token expired
        return True

    def mark_as_used(self):
        """Markiert den Token als verwendet."""
        self.used_at = datetime.utcnow()


class UserContainer(db.Model):
    """Mehrere Container pro Benutzer (Multi-Container-Unterstützung)."""
    __tablename__ = 'user_container'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    container_type = db.Column(db.String(50), nullable=False)
    container_id = db.Column(db.String(100), unique=True)
    container_port = db.Column(db.Integer)
    template_image = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

    # Container lifecycle status (not_created, running, stopped, error)
    status = db.Column(db.String(20), default='not_created', nullable=False)

    # Container blocking
    is_blocked = db.Column(db.Boolean, default=False, nullable=False, index=True)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    # Relationships (explicit primaryjoin due to multiple FKs to User)
    user = db.relationship('User',
                          primaryjoin='UserContainer.user_id==User.id',
                          back_populates='containers')
    blocker = db.relationship('User',
                             primaryjoin='UserContainer.blocked_by==User.id')

    # Unique: one container per type per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'container_type', name='uq_user_container_type'),
    )

    def to_dict(self):
        """Convert UserContainer to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'container_type': self.container_type,
            'container_id': self.container_id,
            'container_port': self.container_port,
            'template_image': self.template_image,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'status': self.status,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None
        }


class AdminTakeoverSession(db.Model):
    """Logs admin access to user containers"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(500), nullable=True)

    admin = db.relationship('User', foreign_keys=[admin_id],
                           backref=db.backref('takeover_sessions_as_admin', lazy=True))
    target_user = db.relationship('User', foreign_keys=[target_user_id],
                                 backref=db.backref('takeover_sessions_as_target', lazy=True, cascade='all, delete-orphan'))


class EmailRule(db.Model):
    """Whitelist/Blacklist-Regeln für E-Mail-Registrierung."""
    __tablename__ = 'email_rule'

    id = db.Column(db.Integer, primary_key=True)
    pattern = db.Column(db.String(255), nullable=False)
    rule_type = db.Column(db.String(10), nullable=False)  # 'whitelist' or 'blacklist'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    creator = db.relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        db.UniqueConstraint('pattern', 'rule_type', name='uq_email_rule_pattern_type'),
    )

    def to_dict(self):
        """Konvertiert die Regel in ein Dictionary für API-Antworten."""
        return {
            'id': self.id,
            'pattern': self.pattern,
            'rule_type': self.rule_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
        }
