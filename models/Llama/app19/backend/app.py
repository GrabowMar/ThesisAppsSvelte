# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import hashlib

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# Create a SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create tables if they do not exist
def create_tables():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, balance REAL, address TEXT)
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions
        (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER, amount REAL, timestamp TEXT)
    ''')
    conn.close()

create_tables()

# 4. Authentication Logic (if needed)
def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user and user['password'] == hashlib.sha256(password.encode()).hexdigest():
        return user
    return None

# 5. Utility Functions
def get_user_balance(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
    return user['balance']

def update_user_balance(user_id, amount):
    conn = get_db_connection()
    conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# 6. API Routes
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    password = request.json['password']
    address = request.json['address']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if user:
        return jsonify({'error': 'Username already exists'}), 400
    conn.execute('INSERT INTO users (username, password, balance, address) VALUES (?, ?, 0, ?)',
                  (username, hashlib.sha256(password.encode()).hexdigest(), address))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    user = authenticate_user(username, password)
    if user:
        return jsonify({'user_id': user['id'], 'balance': get_user_balance(user['id'])}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/send', methods=['POST'])
def send():
    sender_id = request.json['sender_id']
    receiver_id = request.json['receiver_id']
    amount = request.json['amount']
    if get_user_balance(sender_id) < amount:
        return jsonify({'error': 'Insufficient balance'}), 400
    update_user_balance(sender_id, -amount)
    update_user_balance(receiver_id, amount)
    conn = get_db_connection()
    conn.execute('INSERT INTO transactions (sender_id, receiver_id, amount, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                  (sender_id, receiver_id, amount))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Transaction successful'}), 200

@app.route('/balance', methods=['GET'])
def balance():
    user_id = request.args.get('user_id')
    return jsonify({'balance': get_user_balance(user_id)}), 200

@app.route('/transactions', methods=['GET'])
def transactions():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id)).fetchall()
    conn.close()
    return jsonify([dict(transaction) for transaction in transactions]), 200

@app.route('/address', methods=['GET'])
def address():
    user_id = request.args.get('user_id')
    conn = get_db_connection()
    address = conn.execute('SELECT address FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return jsonify({'address': address['address']}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5037')))
