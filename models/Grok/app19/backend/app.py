# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os
import jwt
import datetime
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # Secret key for session management
bcrypt = Bcrypt(app)

# Mock database (replace with actual database in production)
users = {}
wallets = {}

# 3. Database Models (if needed)
# (Mocked for this example)

# 4. Authentication Logic
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = users.get(data['public_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    user = users.get(auth.username)
    if not user:
        return jsonify({'message': 'User not found'}), 401
    if bcrypt.check_password_hash(user['password'], auth.password):
        token = jwt.encode({'public_id': user['public_id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.secret_key)
        return jsonify({'token': token})
    return jsonify({'message': 'Could not verify'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = {
        'public_id': len(users) + 1,
        'username': data['username'],
        'password': hashed_password
    }
    users[user['username']] = user
    wallets[user['username']] = {'balance': 0, 'transactions': [], 'addresses': []}
    return jsonify({'message': 'User created successfully'}), 201

# 5. Utility Functions
def generate_address():
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(34))

# 6. API Routes
@app.route('/api/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    return jsonify({'balance': wallets[current_user['username']]['balance']})

@app.route('/api/send', methods=['POST'])
@token_required
def send_crypto(current_user):
    data = request.get_json()
    if 'amount' not in data or 'to' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    amount = float(data['amount'])
    to_user = data['to']
    if to_user not in users:
        return jsonify({'message': 'Recipient not found'}), 404
    if wallets[current_user['username']]['balance'] < amount:
        return jsonify({'message': 'Insufficient funds'}), 400
    wallets[current_user['username']]['balance'] -= amount
    wallets[to_user]['balance'] += amount
    wallets[current_user['username']]['transactions'].append({
        'type': 'send',
        'amount': amount,
        'to': to_user,
        'timestamp': datetime.datetime.now().isoformat()
    })
    wallets[to_user]['transactions'].append({
        'type': 'receive',
        'amount': amount,
        'from': current_user['username'],
        'timestamp': datetime.datetime.now().isoformat()
    })
    return jsonify({'message': 'Transaction successful'}), 200

@app.route('/api/receive', methods=['POST'])
@token_required
def receive_crypto(current_user):
    data = request.get_json()
    if 'amount' not in data or 'from' not in data:
        return jsonify({'message': 'Missing required fields'}), 400
    amount = float(data['amount'])
    from_user = data['from']
    if from_user not in users:
        return jsonify({'message': 'Sender not found'}), 404
    if wallets[from_user]['balance'] < amount:
        return jsonify({'message': 'Insufficient funds'}), 400
    wallets[from_user]['balance'] -= amount
    wallets[current_user['username']]['balance'] += amount
    wallets[from_user]['transactions'].append({
        'type': 'send',
        'amount': amount,
        'to': current_user['username'],
        'timestamp': datetime.datetime.now().isoformat()
    })
    wallets[current_user['username']]['transactions'].append({
        'type': 'receive',
        'amount': amount,
        'from': from_user,
        'timestamp': datetime.datetime.now().isoformat()
    })
    return jsonify({'message': 'Transaction successful'}), 200

@app.route('/api/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    return jsonify(wallets[current_user['username']]['transactions'])

@app.route('/api/addresses', methods=['GET', 'POST'])
@token_required
def manage_addresses(current_user):
    if request.method == 'GET':
        return jsonify(wallets[current_user['username']]['addresses'])
    elif request.method == 'POST':
        new_address = generate_address()
        wallets[current_user['username']]['addresses'].append(new_address)
        return jsonify({'message': 'New address generated', 'address': new_address}), 201

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found', 'error': str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error', 'error': str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6017')))
