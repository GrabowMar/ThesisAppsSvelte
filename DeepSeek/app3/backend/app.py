# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
from werkzeug.security import generate_password_hash, check_password_hash

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS with credentials
app.secret_key = os.urandom(24)  # Secret key for session management

# 3. Mock Database (for demonstration purposes)
users_db = {}

# 4. Utility Functions
def validate_user_data(data):
    """Validate user registration data."""
    if not data.get('username') or not data.get('password'):
        return False
    return True

# 5. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    if not validate_user_data(data):
        return jsonify({"error": "Invalid input"}), 400

    username = data['username']
    if username in users_db:
        return jsonify({"error": "Username already exists"}), 400

    password_hash = generate_password_hash(data['password'])
    users_db[username] = password_hash
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Log in a user."""
    data = request.get_json()
    if not validate_user_data(data):
        return jsonify({"error": "Invalid input"}), 400

    username = data['username']
    password = data['password']
    if username not in users_db or not check_password_hash(users_db[username], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session['username'] = username  # Store username in session
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.pop('username', None)
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if the user is authenticated."""
    if 'username' in session:
        return jsonify({"authenticated": True, "username": session['username']}), 200
    return jsonify({"authenticated": False}), 401

# 6. Error Handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

# 7. Start the App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5161')))