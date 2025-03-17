# Import required libraries
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

# Create a new Flask application
app = Flask(__name__)
CORS(app)

# Configure MySQL database connection
db_host = 'localhost'
db_user = 'root'
db_password = 'password'
db_name = 'auth_system'

# Create a connection to the database
cnx = mysql.connector.connect(
    user=db_user,
    password=db_password,
    host=db_host,
    database=db_name
)

# Create a cursor object to execute SQL queries
cursor = cnx.cursor()

# Define a function to create a new user
def create_user(username, email, password):
    hashed_password = generate_password_hash(password)
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, email, hashed_password))
    cnx.commit()

# Define a function to check if a user exists
def user_exists(username):
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    return cursor.fetchone() is not None

# Define a function to verify user credentials
def verify_credentials(username, password):
    query = "SELECT password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    hashed_password = cursor.fetchone()[0]
    return check_password_hash(hashed_password, password)

# Define routes for the application
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    if user_exists(username):
        return jsonify({'error': 'User already exists'}), 400
    create_user(username, email, password)
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    if not user_exists(username):
        return jsonify({'error': 'User does not exist'}), 400
    if not verify_credentials(username, password):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['username'] = username
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'message': f'Welcome, {session["username"]}'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logged out successfully'}), 200

# Run the application
if __name__ == '__main__':
    app.secret_key = 'secret_key'
    app.run(port=5001)
