# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
from datetime import timedelta
import re
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)  # Generate a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days

# Enable CORS
CORS(app, supports_credentials=True, origins=["http://localhost:5821"])

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# 4. Authentication Logic
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 5. Utility Functions
def is_valid_email(email):
    """Validate email format using regex"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def is_strong_password(password):
    """Check if password meets security requirements"""
    # At least 8 characters, contains letters, numbers, and special characters
    if len(password) < 8:
        return False
        
    has_letter = False
    has_number = False
    has_special = False
    
    for char in password:
        if char.isalpha():
            has_letter = True
        elif char.isdigit():
            has_number = True
        elif not char.isalnum():
            has_special = True
    
    return has_letter and has_number and has_special

# Create all tables
with app.app_context():
    db.create_all()

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Input validation
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
        
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
        
    if not is_strong_password(password):
        return jsonify({"error": "Password must be at least 8 characters and include letters, numbers, and special characters"}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409
        
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409
    
    # Hash password and create new user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Registration successful"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed. Please try again."}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.get_json()
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Input validation
    if not username_or_email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    # Find user by username or email
    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        # Create session
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    """Get current user information"""
    user = User.query.get(session['user_id'])
    
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }), 200
    
    return jsonify({"authenticated": False}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5321')), debug=True)
