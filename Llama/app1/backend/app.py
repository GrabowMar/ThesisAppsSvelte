# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3

# 2. App Configuration
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)

# 3. Database Connection
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create table
c.execute("""CREATE TABLE IF NOT EXISTS users
             (username text, password text)""")

conn.commit()
conn.close()

# 4. Utility Functions
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def register_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    if c.fetchone():
        return False
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, generate_password_hash(password)))
    conn.commit()
    conn.close()
    return True

def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user and check_password_hash(user['password'], password):
        return True
    return False

# 5. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if register_user(username, password):
        return jsonify({'message': 'User registered successfully'}), 201
    return jsonify({'message': 'User already exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if login_user(username, password):
        session['username'] = username
        return jsonify({'message': 'User logged in successfully'}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    if 'username' in session:
        return jsonify({'message': 'Welcome to the dashboard'}), 200
    return jsonify({'message': 'Please login first'}), 401

# 6. Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'Page not found'}), 404

# 7. Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5001')))
