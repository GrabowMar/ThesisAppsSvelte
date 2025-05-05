# 1. Imports Section
from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from functools import wraps
import os
import jwt
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.urandom(24)
bcrypt = Bcrypt(app)

# 3. Database Models (in-memory for simplicity, use a real database in production)
users = {}

# 4. Authentication Logic
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# 5. Utility Functions
def generate_token(user_id):
    return jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if data['username'] in users:
        return jsonify({'message': 'Username already exists'}), 400
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    users[data['username']] = {'password': hashed_password}
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users.get(data['username'])
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        token = generate_token(data['username'])
        return jsonify({'token': token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/dashboard', methods=['GET'])
@token_required
def dashboard():
    return jsonify({'message': 'Dashboard accessed successfully'}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5481')))
