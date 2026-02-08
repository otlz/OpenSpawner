from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
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
    email = db.Column(db.String(120), unique=True, nullable=False)
    slug = db.Column(db.String(12), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Admin-Felder
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Sperr-Felder
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Email-Verifizierung und Status
    state = db.Column(db.String(20), default=UserState.REGISTERED.value, nullable=False)

    # Aktivitaetstracking
    last_used = db.Column(db.DateTime, nullable=True)

    # Beziehung fuer blocked_by
    blocker = db.relationship('User', remote_side=[id], foreign_keys=[blocked_by])

    # Multi-Container Support (explicit primaryjoin wegen mehrerer FKs zu User)
    containers = db.relationship('UserContainer',
                                foreign_keys=['UserContainer.user_id'],
                                primaryjoin='User.id==UserContainer.user_id',
                                back_populates='user',
                                cascade='all, delete-orphan')

    @property
    def container_id(self):
        """Backwards compatibility: gibt ID des Primary Containers zurück"""
        if self.containers:
            return self.containers[0].container_id
        return None

    @container_id.setter
    def container_id(self, value):
        """Backwards compatibility: setzt Primary Container ID"""
        if not self.containers:
            # Erstelle Primary Container wenn nicht vorhanden
            from config import Config
            primary = UserContainer(
                user_id=self.id,
                container_type='template-01',
                template_image=Config.USER_TEMPLATE_IMAGE
            )
            db.session.add(primary)
            db.session.flush()
            self.containers.append(primary)
        self.containers[0].container_id = value

    @property
    def container_port(self):
        """Backwards compatibility: gibt Port des Primary Containers zurück"""
        if self.containers:
            return self.containers[0].container_port
        return None

    @container_port.setter
    def container_port(self, value):
        """Backwards compatibility: setzt Primary Container Port"""
        if not self.containers:
            # Erstelle Primary Container wenn nicht vorhanden
            from config import Config
            primary = UserContainer(
                user_id=self.id,
                container_type='template-01',
                template_image=Config.USER_TEMPLATE_IMAGE
            )
            db.session.add(primary)
            db.session.flush()
            self.containers.append(primary)
        self.containers[0].container_port = value

    def to_dict(self):
        """Konvertiert User zu Dictionary fuer API-Responses"""
        return {
            'id': self.id,
            'email': self.email,
            'slug': self.slug,
            'is_admin': self.is_admin,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'state': self.state,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'container_id': self.container_id
        }


class MagicLinkToken(db.Model):
    """Magic Link Tokens für Passwordless Authentication"""
    __tablename__ = 'magic_link_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    token_type = db.Column(db.String(20), nullable=False)  # 'signup' oder 'login'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship('User', backref=db.backref('magic_tokens', lazy=True, cascade='all, delete-orphan'))

    def is_valid(self):
        """Prüft ob Token noch gültig ist"""
        if self.used_at is not None:
            return False  # Token bereits verwendet
        if datetime.utcnow() > self.expires_at:
            return False  # Token abgelaufen
        return True

    def mark_as_used(self):
        """Markiert Token als verwendet"""
        self.used_at = datetime.utcnow()


class UserContainer(db.Model):
    """Multi-Container pro User (dev und prod)"""
    __tablename__ = 'user_container'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    container_type = db.Column(db.String(50), nullable=False)  # 'dev' oder 'prod'
    container_id = db.Column(db.String(100), unique=True)
    container_port = db.Column(db.Integer)
    template_image = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)

    # Container Blocking (Phase 7)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False, index=True)
    blocked_at = db.Column(db.DateTime, nullable=True)
    blocked_by = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    # Relationships (explicit primaryjoin wegen mehrerer FKs zu User)
    user = db.relationship('User',
                          foreign_keys=['user_id'],
                          primaryjoin='UserContainer.user_id==User.id',
                          back_populates='containers')
    blocker = db.relationship('User',
                             foreign_keys=['blocked_by'],
                             primaryjoin='UserContainer.blocked_by==User.id')

    # Unique: Ein User kann nur einen Container pro Typ haben
    __table_args__ = (
        db.UniqueConstraint('user_id', 'container_type', name='uq_user_container_type'),
    )

    def to_dict(self):
        """Konvertiert UserContainer zu Dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'container_type': self.container_type,
            'container_id': self.container_id,
            'container_port': self.container_port,
            'template_image': self.template_image,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_blocked': self.is_blocked,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None
        }


class AdminTakeoverSession(db.Model):
    """Protokolliert Admin-Zugriffe auf User-Container (Phase 2)"""
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