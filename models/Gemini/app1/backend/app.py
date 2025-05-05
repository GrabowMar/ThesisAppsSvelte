# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import bcrypt
import secrets

# 2. App Configuration
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a strong secret key
CORS(app, supports_credentials=True) # Allow CORS for all origins and credentials

# In-memory user database (replace with a real database in production)
users = {}

# 5. Utility Functions

def hash_password(password):
    """Hashes a password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    """Checks if a password matches a hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


# 6. API Routes

@app.route('/api/register', methods=['POST'])
def register():
    """Registers a new user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'message': 'Username already exists'}), 409

    hashed_password = hash_password(password)
    users[username] = {'password': hashed_password}

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/api/login', methods=['POST'])
def login():
    """Logs in an existing user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if username not in users:
        return jsonify({'message': 'Invalid username or password'}), 401

    user = users[username]
    if check_password(password, user['password']):
        session['username'] = username  # Store username in session
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logs out the current user."""
    session.pop('username', None)  # Remove username from session
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    """Returns a dashboard message if the user is logged in."""
    if 'username' in session:
        return jsonify({'message': f'Welcome to the dashboard, {session["username"]}!'}), 200
    else:
        return jsonify({'message': 'Unauthorized'}), 401

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    """Checks if the user is authenticated."""
    if 'username' in session:
        return jsonify({'username': session['username']}), 200
    else:
        return jsonify({'username': None}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5401')), debug=True)
