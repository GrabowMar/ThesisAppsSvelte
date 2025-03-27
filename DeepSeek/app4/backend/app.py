from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import hashlib

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # Secret key for session management

# In-memory database for demonstration purposes
users = {}

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Route for user registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = hash_password(password)
    users[username] = hashed_password
    return jsonify({'message': 'User registered successfully'}), 201

# Route for user login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    hashed_password = hash_password(password)

    if username not in users or users[username] != hashed_password:
        return jsonify({'error': 'Invalid username or password'}), 401

    session['username'] = username
    return jsonify({'message': 'Login successful'}), 200

# Route for checking session
@app.route('/api/check-session', methods=['GET'])
def check_session():
    if 'username' in session:
        return jsonify({'username': session['username']}), 200
    return jsonify({'error': 'Not logged in'}), 401

# Route for user logout
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

# Error handler for 500
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5161')))
