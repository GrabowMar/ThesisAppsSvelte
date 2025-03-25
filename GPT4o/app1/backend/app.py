from flask import Flask, request, jsonify, session, redirect
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_session import Session
import uuid

app = Flask(__name__)

# Configuration for the Flask app
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this in production!
app.config['SESSION_TYPE'] = 'filesystem'
SESSION_COOKIE_NAME = "session_app"

# Allow access from frontend (CORS)
CORS(app, supports_credentials=True)

# Initialize bcrypt and session
bcrypt = Bcrypt(app)
Session(app)

# In-memory database for demonstration (replace with proper DB in production)
users_db = {}

# --- ROUTES ---
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Input validation
        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400

        # Check if user exists
        if username in users_db:
            return jsonify({'error': 'User already exists.'}), 400

        # Hash password securely
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_db[username] = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': hashed_password,
        }

        return jsonify({'message': 'User registered successfully.'}), 201
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Input validation
        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400

        # Check user existence
        user = users_db.get(username)

        if not user or not bcrypt.check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid username or password.'}), 401

        # Set user session
        session['user'] = {'id': user['id'], 'username': user['username']}
        return jsonify({'message': 'Login successful.'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'message': 'Logged out successfully.'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        user = session.get('user')

        if not user:
            return jsonify({'error': 'Unauthorized access'}), 401

        return jsonify({'message': f'Welcome {user["username"]}!', 'user': user}), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# Run the app
if __name__ == '__main__':
    app.run(port=5241, debug=True)
