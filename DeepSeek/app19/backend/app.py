# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (Mocked for Simplicity)
from dataclasses import dataclass
from typing import List

@dataclass
class Transaction:
    tx_id: str
    sender: str
    receiver: str
    amount: float

# Mocked user data
user_balance = 1000.0
user_address = "0x1234567890abcdef"
transaction_history: List[Transaction] = []

# 4. Utility Functions
def generate_transaction_id():
    import uuid
    return str(uuid.uuid4())

# 5. API Routes
@app.route('/api/balance', methods=['GET'])
def get_balance():
    return jsonify({"balance": user_balance, "address": user_address})

@app.route('/api/send', methods=['POST'])
def send_crypto():
    data = request.json
    receiver = data.get("receiver")
    amount = data.get("amount")

    if not receiver or not amount:
        return jsonify({"error": "Receiver and amount are required"}), 400

    if amount > user_balance:
        return jsonify({"error": "Insufficient balance"}), 400

    global user_balance
    user_balance -= amount

    tx = Transaction(
        tx_id=generate_transaction_id(),
        sender=user_address,
        receiver=receiver,
        amount=amount
    )
    transaction_history.append(tx)

    return jsonify({"message": "Transaction successful", "tx_id": tx.tx_id})

@app.route('/api/transactions', methods=['GET'])
def get_transaction_history():
    return jsonify([tx.__dict__ for tx in transaction_history])

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# 7. Start Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5197')))
