# app/backend/app.py
from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

# --- App Configuration ---
app = Flask(__name__)
# In production, load your secret key from an environment variable or config file
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'my-very-secret-key')
# Set session cookie secure parameters if using HTTPS in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Change to True with HTTPS

# Enable CORS for all origins (adjust as needed in production)
CORS(app, supports_credentials=True)

# --- In-memory user "database" ---
users = {}  # format: { username: { "password": hashed_password } }

# --- Utility function ---
def is_authenticated():
    return 'user' in session

# --- API Routes ---

@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user with a username and password.
    """
    try:
        data = request.get_json(force=True)
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required.'}), 400

        if username in users:
            return jsonify({'success': False, 'message': 'Username already exists.'}), 409

        # Securely hash the password
        hashed_password = generate_password_hash(password)
        users[username] = {"password": hashed_password}

        return jsonify({'success': True, 'message': 'Registration successful.'}), 201
    except Exception as e:
        # Log exception as needed in production logging system.
        return jsonify({'success': False, 'message': 'Registration failed.', 'error': str(e)}), 500


@app.route('/login', methods=['POST'])
def login():
    """
    Logs in a user with a valid username/password.
    """
    try:
        data = request.get_json(force=True)
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required.'}), 400

        user = users.get(username)
        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

        if not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid credentials.'}), 401

        # Save the user in session
        session['user'] = username
        return jsonify({'success': True, 'message': 'Login successful.'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Login failed.', 'error': str(e)}), 500


@app.route('/dashboard', methods=['GET'])
def dashboard():
    """
    A protected route for logged in users.
    """
    if not is_authenticated():
        return jsonify({'success': False, 'message': 'Unauthorized access. Please log in.'}), 401

    username = session.get('user')
    return jsonify({'success': True, 'message': f'Welcome to your dashboard, {username}!'}), 200


@app.route('/logout', methods=['POST'])
def logout():
    """
    Logs the user out by clearing the session.
    """
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'message': 'Internal Server Error'}), 500

# --- Main entrypoint ---
if __name__ == '__main__':
    # Use port 6141 for the backend as specified. In production, set PORT as an environment variable.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6141')))
