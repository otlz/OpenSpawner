from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from container_manager import ContainerManager

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User-Login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Container spawnen wenn noch nicht vorhanden
            if not user.container_id:
                try:
                    container_mgr = ContainerManager()
                    container_id, port = container_mgr.spawn_container(user.id, user.username)
                    user.container_id = container_id
                    user.container_port = port
                    db.session.commit()
                except Exception as e:
                    flash(f'Container-Start fehlgeschlagen: {str(e)}', 'error')
                    return redirect(url_for('auth.login'))
            
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültige Anmeldedaten', 'error')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """User-Registrierung"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Prüfe ob User existiert
        if User.query.filter_by(username=username).first():
            flash('Username bereits vergeben', 'error')
            return redirect(url_for('auth.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email bereits registriert', 'error')
            return redirect(url_for('auth.signup'))
        
        # Neuen User anlegen
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Container aus Template bauen und starten
        try:
            container_mgr = ContainerManager()
            container_id, port = container_mgr.spawn_container(user.id, user.username)
            user.container_id = container_id
            user.container_port = port
            db.session.commit()
            
            flash('Registrierung erfolgreich! Container wird gestartet...', 'success')
            login_user(user)
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.delete(user)
            db.session.commit()
            flash(f'Registrierung fehlgeschlagen: {str(e)}', 'error')
    
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User-Logout"""
    logout_user()
    flash('Erfolgreich abgemeldet', 'success')
    return redirect(url_for('auth.login'))
