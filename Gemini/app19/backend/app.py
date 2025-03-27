# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import secrets  # For generating secure addresses
import datetime  # For timestamping transactions

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Dummy Data (Replace with a real database for production)
wallets = {}  # Address: Balance
transactions = []  # List of transaction dictionaries

# 4. Utility Functions
def generate_address():
    """Generates a new unique crypto address."""
    return secrets.token_hex(20)  # 20 bytes = 40 hex characters


def validate_address(address):
    """Basic address validation (length check)."""
    return len(address) == 40 and all(c in '0123456789abcdef' for c in address)


# 5. API Routes

@app.route('/api/create_wallet', methods=['POST'])
def create_wallet():
    """Creates a new wallet with a unique address and initial balance."""
    address = generate_address()
    wallets[address] = 0  # Initial balance
    return jsonify({'address': address, 'message': 'Wallet created successfully'}), 201


@app.route('/api/balance/<address>', methods=['GET'])
def get_balance(address):
    """Retrieves the balance for a given wallet address."""
    if address not in wallets:
        return jsonify({'error': 'Wallet not found'}), 404
    return jsonify({'address': address, 'balance': wallets[address]}), 200


@app.route('/api/send', methods=['POST'])
def send_funds():
    """Sends funds from one wallet to another."""
    data = request.get_json()
    sender_address = data.get('sender')
    recipient_address = data.get('recipient')
    amount = data.get('amount')

    if not all([sender_address, recipient_address, amount]):
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be positive'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount'}), 400

    if sender_address not in wallets:
        return jsonify({'error': 'Sender wallet not found'}), 404
    if recipient_address not in wallets:
        return jsonify({'error': 'Recipient wallet not found'}), 404

    if wallets[sender_address] < amount:
        return jsonify({'error': 'Insufficient funds'}), 400

    wallets[sender_address] -= amount
    wallets[recipient_address] = wallets.get(recipient_address, 0) + amount  # create wallet if doesn't exist
    timestamp = datetime.datetime.now().isoformat()
    transaction = {
        'sender': sender_address,
        'recipient': recipient_address,
        'amount': amount,
        'timestamp': timestamp
    }
    transactions.append(transaction)
    return jsonify({'message': 'Funds sent successfully', 'transaction': transaction}), 200


@app.route('/api/transactions/<address>', methods=['GET'])
def get_transactions(address):
    """Retrieves the transaction history for a given wallet address."""
    wallet_transactions = [
        tx for tx in transactions
        if tx['sender'] == address or tx['recipient'] == address
    ]
    return jsonify({'address': address, 'transactions': wallet_transactions}), 200

@app.route('/api/receive', methods=['POST'])
def receive_funds():
     """Simulates receiving funds (mostly for demonstration)."""
     data = request.get_json()
     recipient_address = data.get('recipient')
     amount = data.get('amount')

     if not all([recipient_address, amount]):
         return jsonify({'error': 'Missing parameters'}), 400

     try:
         amount = float(amount)
         if amount <= 0:
             return jsonify({'error': 'Amount must be positive'}), 400
     except ValueError:
         return jsonify({'error': 'Invalid amount'}), 400

     if recipient_address not in wallets:
         wallets[recipient_address] = 0  # Create the wallet if it doesn't exist

     wallets[recipient_address] += amount
     timestamp = datetime.datetime.now().isoformat()
     transaction = {
         'sender': 'N/A (Received)',  # Denotes a receive transaction
         'recipient': recipient_address,
         'amount': amount,
         'timestamp': timestamp
     }
     transactions.append(transaction)

     return jsonify({'message': 'Funds received successfully', 'transaction': transaction}), 200

# 6. Error Handlers (Example)
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


# 7. Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5437')))
