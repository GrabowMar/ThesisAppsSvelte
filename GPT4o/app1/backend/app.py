from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Flask configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')  # Secure loading of secret key
PORT = int(os.getenv('PORT', 5241))

# In-memory database for demo purposes
users = {}

# Utility Functions
def is_authenticated():
    return 'user' in session

# Routes
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'User already exists'}), 400

    # Store hashed password using Werkzeug for better security
    hashed_password = generate_password_hash(password)
    users[username] = hashed_password
    return jsonify({'message': f'User {username} registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    stored_password = users.get(username)
    if not stored_password or not check_password_hash(stored_password, password):
        return jsonify({'error': 'Invalid credentials'}), 401

    # Set session
    session['user'] = username
    return jsonify({'message': f'Welcome {username}!', 'username': username}), 200

@app.route('/api/logout', methods=['POST'])
def logout_user():
    session.pop('user', None)
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized access, please login'}), 401
    return jsonify({'message': f'Welcome to your dashboard, {session["user"]}'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)