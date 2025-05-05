# 1. Imports
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import time

# 2. App Configuration
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:6097"}})

# 3. In-Memory Database
users = {}
transactions = []

# 4. Authentication Logic
def verify_token(username, token):
    user = users.get(username)
    return user and user['token'] == token

# 5. Utility Functions
def get_user_transactions(username):
    return [t for t in transactions if t['sender'] == username or t['receiver'] == username]

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users.get(data['username'])
    
    if user and check_password_hash(user['password'], data['password']):
        token = str(uuid.uuid4())
        user['token'] = token
        return jsonify({'token': token, 'username': user['username']})
    return make_response('Invalid credentials', 401)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if users.get(data['username']):
        return make_response('Username exists', 400)
        
    users[data['username']] = {
        'username': data['username'],
        'password': generate_password_hash(data['password']),
        'balance': 100.0,  # Initial balance
        'addresses': [],
        'token': None
    }
    return jsonify({'message': 'User created'})

@app.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    token = request.headers.get('Authorization')
    if not verify_token(username, token):
        return make_response('Unauthorized', 401)
        
    user = users.get(username)
    return jsonify({
        'balance': user['balance'],
        'addresses': user['addresses'],
        'transactions': get_user_transactions(username)
    })

@app.route('/api/send', methods=['POST'])
def send_funds():
    data = request.get_json()
    sender = data['sender']
    token = request.headers.get('Authorization')
    
    if not verify_token(sender, token):
        return make_response('Unauthorized', 401)
        
    sender_user = users[sender]
    recipient_user = users.get(data['receiver'])
    
    if not recipient_user:
        return make_response('Recipient not found', 400)
    if sender_user['balance'] < data['amount']:
        return make_response('Insufficient funds', 400)
        
    # Update balances
    sender_user['balance'] -= data['amount']
    recipient_user['balance'] += data['amount']
    
    # Record transaction
    transactions.append({
        'sender': sender,
        'receiver': data['receiver'],
        'amount': data['amount'],
        'timestamp': int(time.time())
    })
    
    return jsonify({'newBalance': sender_user['balance']})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Endpoint not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5597')))
