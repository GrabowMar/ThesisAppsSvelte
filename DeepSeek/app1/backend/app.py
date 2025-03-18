from flask import Flask, request, jsonify, session
from flask_cors import CORS
import hashlib

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'supersecretkey'  # Replace with a secure secret key in production

# Mock database to store users (Replace with a real database in production)
users = {}

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'Username already exists'}), 409

    users[username] = {'password': hash_password(password)}
    return jsonify({'message': 'User registered successfully'}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = users.get(username)
    if not user or user['password'] != hash_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    session['username'] = username
    return jsonify({
        'message': 'Login successful',
        'username': username
    }), 200

# Logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Protected route example
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'message': f'Welcome to the dashboard, {session["username"]}!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5161)
