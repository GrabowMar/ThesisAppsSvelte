# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import bcrypt
import sqlite3
import re
from datetime import datetime, timedelta
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
# Use a strong random secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SECURE'] = True  # For HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['DATABASE'] = 'auth_database.db'

# 3. Database Models/Setup
def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with the users table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# 5. Utility Functions
def validate_registration_input(username, email, password):
    """Validate registration input data."""
    errors = {}
    
    # Username validation
    if not username or len(username) < 3:
        errors['username'] = "Username must be at least 3 characters long"
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = "Username can only contain letters, numbers, and underscores"
    
    # Email validation
    if not email:
        errors['email'] = "Email is required"
    elif not re.match(r'^[\w.-]+@[a-zA-Z\d.-]+\.[a-zA-Z]{2,}$', email):
        errors['email'] = "Invalid email format"
    
    # Password validation
    if not password or len(password) < 8:
        errors['password'] = "Password must be at least 8 characters long"
    elif not re.search(r'[A-Z]', password):
        errors['password'] = "Password must contain at least one uppercase letter"
    elif not re.search(r'[a-z]', password):
        errors['password'] = "Password must contain at least one lowercase letter"
    elif not re.search(r'[0-9]', password):
        errors['password'] = "Password must contain at least one number"
    
    return errors

def user_exists(username=None, email=None):
    """Check if a user with the given username or email exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if username:
        cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return True
    
    if email:
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return True
    
    conn.close()
    return False

def hash_password(password):
    """Hash a password using bcrypt."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(hashed_password, plain_password):
    """Check if the plain password matches the hashed one."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# 4. Authentication Logic
def login_required(f):
    """Decorator function to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_by_id(user_id):
    """Get user details by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user:
        # Convert row to dict
        return dict(user)
    return None

def get_user_by_credentials(username_or_email, password):
    """Authenticate a user by username/email and password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if input is an email or username
    if '@' in username_or_email:
        cursor.execute("SELECT id, username, password_hash FROM users WHERE email = ?", (username_or_email,))
    else:
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username_or_email,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password(user['password_hash'], password):
        return {'id': user['id'], 'username': user['username']}
    
    return None

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        validation_errors = validate_registration_input(username, email, password)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Check if username or email already exists
        if user_exists(username=username):
            return jsonify({'error': 'Username already exists'}), 409
        
        if user_exists(email=email):
            return jsonify({'error': 'Email already exists'}), 409
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Store user in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Registration successful',
            'user': {'username': username, 'email': email}
        }), 201
    
    except Exception as e:
        app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during registration'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Log in a user and create a session."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        # Authenticate user
        user = get_user_by_credentials(username_or_email, password)
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create session
        session.permanent = True
        session['user_id'] = user['id']
        
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user['id'], 'username': user['username']}
        }), 200
    
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during login'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    try:
        # Clear session
        session.pop('user_id', None)
        return jsonify({'message': 'Logout successful'}), 200
    
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred during logout'}), 500

@app.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    """Get details of the currently logged-in user."""
    try:
        user_id = session.get('user_id')
        user = get_user_by_id(user_id)
        
        if not user:
            session.pop('user_id', None)  # Clear invalid session
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at']
            }
        }), 200
    
    except Exception as e:
        app.logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while retrieving user data'}), 500

@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Protected dashboard data endpoint."""
    try:
        user_id = session.get('user_id')
        user = get_user_by_id(user_id)
        
        if not user:
            session.pop('user_id', None)  # Clear invalid session
            return jsonify({'error': 'User not found'}), 404
        
        # Here you would typically return dashboard-specific data
        dashboard_data = {
            'welcomeMessage': f"Welcome, {user['username']}!",
            'lastLogin': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'stats': {
                'visits': 42,  # Placeholder data
                'activities': 7
            }
        }
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username']
            },
            'dashboardData': dashboard_data
        }), 200
    
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred while retrieving dashboard data'}), 500

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5001')))
