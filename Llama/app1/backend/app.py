# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import bcrypt
import jwt
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret_key'

# 3. Database Models (if needed)
# For simplicity, we'll use a dictionary to store users
users = {}

# 4. Authentication Logic (if needed)
def authenticate_user(username, password):
    if username in users:
        return bcrypt.checkpw(password.encode('utf-8'), users[username]['password'])
    return False

# 5. Utility Functions
def generate_token(username):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': username
    }
    return jwt.encode(
        payload,
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

# 6. API Routes
@app.route('/register', methods=['POST'])
def register_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username in users:
        return jsonify({'error': 'Username already exists'}), 400
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users[username] = {'password': hashed_password}
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if not authenticate_user(username, password):
        return jsonify({'error': 'Invalid username or password'}), 401
    token = generate_token(username)
    return jsonify({'token': token}), 200

@app.route('/protected', methods=['GET'])
def protected_route():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Unauthorized'}), 401
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    return jsonify({'message': 'Hello, ' + payload['sub']}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
