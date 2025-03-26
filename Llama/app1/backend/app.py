# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
bcrypt = Bcrypt(app)

# 3. Database Models (if needed)
users = {}

# 4. Authentication Logic (if needed)
def authenticate_user(username, password):
    if username in users:
        return bcrypt.check_password_hash(users[username]['password'], password)
    return False

# 5. Utility Functions
def register_user(username, password):
    if username in users:
        return False
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    users[username] = {'password': hashed_password}
    return True

# 6. API Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if register_user(data['username'], data['password']):
        return jsonify({'message': 'User registered successfully'}), 201
    return jsonify({'message': 'Username already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if authenticate_user(data['username'], data['password']):
        session['username'] = data['username']
        return jsonify({'message': 'User logged in successfully'}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' in session:
        return jsonify({'message': 'Welcome to the dashboard'}), 200
    return jsonify({'message': 'You are not logged in'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    if 'username' in session:
        session.pop('username', None)
        return jsonify({'message': 'User logged out successfully'}), 200
    return jsonify({'message': 'You are not logged in'}), 401

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Route not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5001')))
