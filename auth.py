"""
Simple authentication system for video automation app
"""
from flask import session, jsonify, request
from functools import wraps
import os
import secrets
import hashlib

# In production, store this in database
# For now, use environment variable
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')

def hash_password(password):
    """Hash password with salt"""
    # In production, use bcrypt or argon2
    salt = "video_automation_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def check_auth():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not check_auth():
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def setup_auth_routes(app):
    """Setup authentication routes"""
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Login with password"""
        data = request.json
        password = data.get('password', '')
        
        # Check if password is set
        if not ADMIN_PASSWORD_HASH:
            # First time - set the password
            if password:
                hashed = hash_password(password)
                return jsonify({
                    'success': True, 
                    'message': 'Password set! Add this to your .env file:',
                    'envVar': f'ADMIN_PASSWORD_HASH={hashed}'
                })
            else:
                return jsonify({'success': False, 'error': 'Please set a password'})
        
        # Verify password
        if hash_password(password) == ADMIN_PASSWORD_HASH:
            session['authenticated'] = True
            session.permanent = True
            return jsonify({'success': True, 'message': 'Logged in successfully'})
        else:
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
    
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        """Logout"""
        session.pop('authenticated', None)
        return jsonify({'success': True, 'message': 'Logged out'})
    
    @app.route('/api/auth/status')
    def auth_status():
        """Check authentication status"""
        return jsonify({
            'authenticated': check_auth(),
            'passwordSet': bool(ADMIN_PASSWORD_HASH)
        })

# Optional: Use for public deployment
USE_AUTH = os.environ.get('USE_AUTH', 'false').lower() == 'true'