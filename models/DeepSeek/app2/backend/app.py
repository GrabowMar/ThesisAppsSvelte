# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # Secret key for session management

# In-memory "database" for demonstration purposes
users = {}

# 3. Utility Functions
def validate_user_input(username, password):
    """Validate user input for registration and login."""
    if not username or not password:
        return False, "Username and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

# 4. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate input
    is_valid, message = validate_user_input(username, password)
    if not is_valid:
        return jsonify({"message": message}), 400

    # Check if user already exists
    if username in users:
        return jsonify({"message": "Username already exists."}), 400

    # Hash password and store user
    users[username] = {
        "password_hash": generate_password_hash(password),
        "username": username
    }
    return jsonify({"message": "User registered successfully."}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Log in an existing user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Validate input
    is_valid, message = validate_user_input(username, password)
    if not is_valid:
        return jsonify({"message": message}), 400

    # Check if user exists
    if username not in users:
        return jsonify({"message": "Invalid username or password."}), 401

    # Verify password
    user = users[username]
    if not check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Invalid username or password."}), 401

    # Create session
    session['username'] = username
    return jsonify({"message": "Login successful."}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully."}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if the user is authenticated."""
    if 'username' in session:
        return jsonify({"authenticated": True, "username": session['username']}), 200
    return jsonify({"authenticated": False}), 200

# 5. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"message": "Internal server error."}), 500

# 6. Run the App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5161')))
