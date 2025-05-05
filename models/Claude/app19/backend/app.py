from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import jwt
import datetime
from functools import wraps

# App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(days=7)
CORS(app)

# In-memory database for demonstration
# In production, use a proper database like PostgreSQL or MongoDB
users_db = {}
wallets_db = {}
transactions_db = []
addresses_db = {}

# Utility Functions
def generate_wallet_address():
    """Generate a unique wallet address"""
    return f"0x{uuid.uuid4().hex[:40]}"

def token_required(f):
    """Decorator for JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users_db.get(data['username'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# API Routes: Authentication
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user with wallet"""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if data['username'] in users_db:
        return jsonify({'message': 'Username already exists'}), 400
    
    # Create user
    hashed_password = generate_password_hash(data['password'])
    users_db[data['username']] = {
        'username': data['username'],
        'password': hashed_password,
        'email': data['email'],
        'created_at': datetime.datetime.now().isoformat()
    }
    
    # Create wallet for user
    wallet_address = generate_wallet_address()
    wallets_db[data['username']] = {
        'address': wallet_address,
        'balance': 1000.0,  # Starting balance for demo purposes
        'created_at': datetime.datetime.now().isoformat()
    }
    
    # Add address to addresses database
    addresses_db[wallet_address] = {
        'owner': data['username'],
        'label': 'Primary Wallet'
    }
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = users_db.get(data['username'])
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate token
    token = jwt.encode({
        'username': user['username'],
        'exp': datetime.datetime.now() + app.config['JWT_EXPIRATION_DELTA']
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'username': user['username'],
        'email': user['email']
    }), 200

# API Routes: Wallet Operations
@app.route('/api/wallet/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    """Get wallet balance for authenticated user"""
    wallet = wallets_db.get(current_user['username'])
    
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    return jsonify({
        'address': wallet['address'],
        'balance': wallet['balance']
    }), 200

@app.route('/api/wallet/address', methods=['GET'])
@token_required
def get_address(current_user):
    """Get wallet address for authenticated user"""
    wallet = wallets_db.get(current_user['username'])
    
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    return jsonify({
        'address': wallet['address']
    }), 200

@app.route('/api/transactions/send', methods=['POST'])
@token_required
def send_crypto(current_user):
    """Send cryptocurrency to another address"""
    data = request.get_json()
    
    if not all(k in data for k in ('to_address', 'amount')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    to_address = data['to_address']
    amount = float(data['amount'])
    
    if amount <= 0:
        return jsonify({'message': 'Amount must be positive'}), 400
    
    wallet = wallets_db.get(current_user['username'])
    
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    if wallet['balance'] < amount:
        return jsonify({'message': 'Insufficient funds'}), 400
    
    # Check if recipient exists
    recipient_exists = False
    recipient_username = None
    
    for username, address_data in addresses_db.items():
        if address_data.get('address') == to_address:
            recipient_exists = True
            recipient_username = username
            break
    
    # Create transaction
    transaction_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    transaction = {
        'id': transaction_id,
        'from_address': wallet['address'],
        'to_address': to_address,
        'amount': amount,
        'timestamp': timestamp,
        'status': 'completed',
        'type': 'send'
    }
    
    # Update balances
    wallet['balance'] -= amount
    
    if recipient_username and recipient_username in wallets_db:
        wallets_db[recipient_username]['balance'] += amount
    
    # Add to transaction history
    transactions_db.append(transaction)
    
    return jsonify({
        'message': 'Transaction completed',
        'transaction_id': transaction_id,
        'timestamp': timestamp,
        'new_balance': wallet['balance']
    }), 200

@app.route('/api/transactions/history', methods=['GET'])
@token_required
def get_transaction_history(current_user):
    """Get transaction history for authenticated user"""
    wallet = wallets_db.get(current_user['username'])
    
    if not wallet:
        return jsonify({'message': 'Wallet not found'}), 404
    
    user_address = wallet['address']
    
    # Filter transactions for this user
    user_transactions = [
        tx for tx in transactions_db 
        if tx['from_address'] == user_address or tx['to_address'] == user_address
    ]
    
    # Add transaction direction for UI
    for tx in user_transactions:
        if tx['from_address'] == user_address:
            tx['direction'] = 'outgoing'
        else:
            tx['direction'] = 'incoming'
    
    # Sort by timestamp (newest first)
    user_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'transactions': user_transactions
    }), 200

@app.route('/api/addresses', methods=['GET'])
@token_required
def get_addresses(current_user):
    """Get saved addresses for authenticated user"""
    username = current_user['username']
    
    # Filter addresses belonging to this user
    user_addresses = {
        address: data for address, data in addresses_db.items()
        if data.get('owner') == username
    }
    
    return jsonify({
        'addresses': [
            {
                'address': address,
                'label': data.get('label', 'Unlabeled')
            }
            for address, data in user_addresses.items()
        ]
    }), 200

@app.route('/api/addresses', methods=['POST'])
@token_required
def add_address(current_user):
    """Add a new address to the user's address book"""
    data = request.get_json()
    
    if not all(k in data for k in ('address', 'label')):
        return jsonify({'message': 'Missing required fields'}), 400
    
    address = data['address']
    label = data['label']
    
    # Add the address to the address book
    addresses_db[address] = {
        'owner': current_user['username'],
        'label': label
    }
    
    return jsonify({
        'message': 'Address added successfully',
        'address': address,
        'label': label
    }), 201

@app.route('/api/addresses/<address>', methods=['DELETE'])
@token_required
def delete_address(current_user, address):
    """Delete an address from the user's address book"""
    if address not in addresses_db or addresses_db[address].get('owner') != current_user['username']:
        return jsonify({'message': 'Address not found'}), 404
    
    # Check if it's not the primary wallet address
    wallet = wallets_db.get(current_user['username'])
    if wallet and wallet['address'] == address:
        return jsonify({'message': 'Cannot delete primary wallet address'}), 400
    
    del addresses_db[address]
    
    return jsonify({
        'message': 'Address deleted successfully'
    }), 200

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5357')), debug=False)
