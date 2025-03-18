from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
import secrets
from datetime import timedelta
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5821"])

# Configure session
app.secret_key = secrets.token_hex(16)  # Generate a secure secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts for 7 days

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

init_db()

# Helper functions
def get_user_by_username(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'password': user[3],
            'created_at': user[4]
        }
    return None

def get_user_by_email(email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'password': user[3],
            'created_at': user[4]
        }
    return None

def is_valid_email(email):
    # Basic email validation pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    # Password requirements: 8+ chars, 1+ number, 1+ uppercase, 1+ lowercase
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    return True, "Password is valid"

# Routes
@app.route('/')
def index():
    return jsonify({'message': 'Authentication API is running'})

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        
        # Validate input
        if not (username and email and password and confirm_password):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        is_valid, password_message = is_valid_password(password)
        if not is_valid:
            return jsonify({'success': False, 'message': password_message}), 400
        
        # Check if username or email already exists
        if get_user_by_username(username):
            return jsonify({'success': False, 'message': 'Username already exists'}), 409
        
        if get_user_by_email(email):
            return jsonify({'success': False, 'message': 'Email already exists'}), 409
        
        # Create new user
        hashed_password = generate_password_hash(password)
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registration successful'}), 201
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during registration'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not (username_or_email and password):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check if username_or_email is an email
        if '@' in username_or_email:
            user = get_user_by_email(username_or_email)
        else:
            user = get_user_by_username(username_or_email)
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid username/email or password'}), 401
        
        if not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid username/email or password'}), 401
        
        # Set session data
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logout successful'}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during logout'}), 500

@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        user_id = session['user_id']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            session.clear()
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'created_at': user[3]
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5321))
    app.run(host='0.0.0.0', port=port, debug=True)