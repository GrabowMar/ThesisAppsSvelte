from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity
users = {}
transactions = []

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = str(uuid.uuid4())
    users[user_id] = {
        'username': data['username'],
        'password': data['password'],  # Note: In a real app, hash the password
        'balance': 0,
        'address': str(uuid.uuid4())
    }
    return jsonify({'user_id': user_id, 'address': users[user_id]['address']}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    for user_id, user in users.items():
        if user['username'] == data['username'] and user['password'] == data['password']:
            return jsonify({'user_id': user_id, 'address': user['address']}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    if user_id in users:
        return jsonify({'balance': users[user_id]['balance']}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/send', methods=['POST'])
def send():
    data = request.get_json()
    sender_id = data['sender_id']
    receiver_address = data['receiver_address']
    amount = data['amount']

    if sender_id not in users:
        return jsonify({'error': 'Sender not found'}), 404

    sender = users[sender_id]
    if sender['balance'] < amount:
        return jsonify({'error': 'Insufficient balance'}), 400

    receiver_id = None
    for user_id, user in users.items():
        if user['address'] == receiver_address:
            receiver_id = user_id
            break

    if receiver_id is None:
        return jsonify({'error': 'Receiver not found'}), 404

    sender['balance'] -= amount
    users[receiver_id]['balance'] += amount

    transactions.append({
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'amount': amount
    })

    return jsonify({'message': 'Transaction successful'}), 200

@app.route('/transactions/<user_id>', methods=['GET'])
def get_transactions(user_id):
    user_transactions = [t for t in transactions if t['sender_id'] == user_id or t['receiver_id'] == user_id]
    return jsonify(user_transactions), 200

if __name__ == '__main__':
    app.run(port=5117)
