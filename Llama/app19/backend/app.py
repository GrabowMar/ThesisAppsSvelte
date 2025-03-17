from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import hashlib
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Create a SQLite database if it doesn't exist
if not os.path.exists('crypto_wallet.db'):
    conn = sqlite3.connect('crypto_wallet.db')
    c = conn.cursor()

    # Create table for users
    c.execute('''CREATE TABLE users
                 (username text, password text, balance real, address text)''')

    # Create table for transactions
    c.execute('''CREATE TABLE transactions
                 (sender text, recipient text, amount real)''')

    conn.commit()
    conn.close()

# Define a function to connect to the database
def connect_to_db():
    conn = sqlite3.connect('crypto_wallet.db')
    c = conn.cursor()
    return c, conn

# Define a route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        c, conn = connect_to_db()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user and hashlib.sha256(password.encode()).hexdigest() == user[1]:
            return jsonify({'success': True, 'balance': user[2], 'address': user[3]})
        else:
            return jsonify({'success': False})
    return render_template('login.html')

# Define a route for the register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        balance = 0.0
        address = 'abc123'  # Generate a random address
        c, conn = connect_to_db()
        c.execute("INSERT INTO users (username, password, balance, address) VALUES (?, ?, ?, ?)", 
                   (username, hashlib.sha256(password.encode()).hexdigest(), balance, address))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return render_template('register.html')

# Define a route for the dashboard page
@app.route('/dashboard', methods=['GET'])
def dashboard():
    c, conn = connect_to_db()
    c.execute("SELECT * FROM transactions")
    transactions = c.fetchall()
    conn.close()
    return render_template('dashboard.html', transactions=transactions)

# Define a route for sending cryptocurrency
@app.route('/send', methods=['POST'])
def send():
    sender = request.form['sender']
    recipient = request.form['recipient']
    amount = float(request.form['amount'])
    c, conn = connect_to_db()
    c.execute("SELECT balance FROM users WHERE username=?", (sender,))
    balance = c.fetchone()[0]
    if balance >= amount:
        c.execute("UPDATE users SET balance=balance-? WHERE username=?", (amount, sender))
        c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, recipient))
        c.execute("INSERT INTO transactions (sender, recipient, amount) VALUES (?, ?, ?)", 
                  (sender, recipient, amount))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

# Define a route for receiving cryptocurrency
@app.route('/receive', methods=['POST'])
def receive():
    recipient = request.form['recipient']
    amount = float(request.form['amount'])
    c, conn = connect_to_db()
    c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, recipient))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Define a route for checking balance
@app.route('/balance', methods=['POST'])
def balance():
    username = request.form['username']
    c, conn = connect_to_db()
    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = c.fetchone()[0]
    conn.close()
    return jsonify({'balance': balance})

# Define a route for address management
@app.route('/address', methods=['POST'])
def address():
    username = request.form['username']
    c, conn = connect_to_db()
    c.execute("SELECT address FROM users WHERE username=?", (username,))
    address = c.fetchone()[0]
    conn.close()
    return jsonify({'address': address})

if __name__ == '__main__':
    app.run(port=5037)
