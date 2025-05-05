from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import random

# Flask app initialization and CORS configuration
app = Flask(__name__)
CORS(app)

# In-memory mock data for simplicity
wallets = {
    "user1": {
        "address": "abc123",
        "balance": 500,  # initial balance in crypto units
        "transactions": []
    }
}

# Utility Functions
def create_transaction(sender, recipient, amount):
    """
    Helper function to create a transaction between sender & recipient.
    """
    transaction_id = random.randint(1000, 9999)  # generate a random transaction ID
    transaction = {
        "transaction_id": transaction_id,
        "sender": sender,
        "recipient": recipient,
        "amount": amount
    }
    return transaction

# ------------------------------------------
# API Routes
# ------------------------------------------

@app.route('/api/get_balance', methods=['GET'])
def get_balance():
    """
    Get the balance of a user wallet.
    """
    user_id = request.args.get("user_id", "user1")  # default to user1
    wallet = wallets.get(user_id)

    if wallet:
        return jsonify({"balance": wallet["balance"]})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/api/send_funds', methods=['POST'])
def send_funds():
    """
    Send funds to another wallet.
    """
    data = request.json
    sender_id = data.get("sender_id")
    recipient = data.get("recipient")
    amount = data.get("amount")
    
    sender_wallet = wallets.get(sender_id)
    if not sender_wallet:
        return jsonify({"error": "Sender wallet not found"}), 404

    if sender_wallet["balance"] < amount:
        return jsonify({"error": "Insufficient funds"}), 400

    # Process transaction
    sender_wallet["balance"] -= amount
    transaction = create_transaction(sender_id, recipient, amount)
    sender_wallet["transactions"].append(transaction)

    return jsonify({"message": "Transaction successful", "transaction": transaction})

@app.route('/api/transaction_history', methods=['GET'])
def transaction_history():
    """
    Get past transactions of a user wallet.
    """
    user_id = request.args.get("user_id", "user1")  # default to user1
    wallet = wallets.get(user_id)

    if wallet:
        transactions = wallet.get("transactions", [])
        return jsonify({"transactions": transactions})
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/api/add_wallet', methods=['POST'])
def add_wallet():
    """
    Add a new wallet.
    """
    data = request.json
    user_id = data.get("user_id")
    address = data.get("address")
    initial_balance = data.get("initial_balance", 0)

    if user_id in wallets:
        return jsonify({"error": "Wallet already exists"}), 400

    wallets[user_id] = {
        "address": address,
        "balance": initial_balance,
        "transactions": []
    }

    return jsonify({"message": "Wallet added successfully"})

# ------------------------------------------
# Error Handlers
# ------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle generic server errors."""
    return jsonify({"error": "Internal server error"}), 500

# Entry point for running Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5277')))
