# 1. Imports Section
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import bcrypt
import uuid
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)

# 3. Temporary Database Storage
users = {}

# 4. Authentication Logic
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# 5. Utility Functions
def generate_session_token():
    return str(uuid.uuid4())

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    if username in users:
        return jsonify({'error': 'Username already exists'}), 400

    hashed_pw = hash_password(password)
    users[username] = {
        'password': hashed_pw,
        'token': None
    }
    return jsonify({'message': 'Registration successful'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users.get(username)
    if not user or not check_password(password, user['password']):
        return jsonify({'error': 'Invalid credentials'}), 401

    token = generate_session_token()
    user['token'] = token
    response = make_response(jsonify({'message': 'Login successful'}))
    response.set_cookie('session_token', token, httponly=True)
    return response

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401

    user = next((u for u in users.values() if u['token'] == token), None)
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    return jsonify({'message': f'Welcome to your dashboard!'}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.cookies.get('session_token')
    user = next((u for u in users.values() if u['token'] == token), None)
    if user:
        user['token'] = None
    
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.delete_cookie('session_token')
    return response

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5561')))
