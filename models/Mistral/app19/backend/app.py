from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Mock database to store user data and transaction history
users = {}
transactions = []

# Utility Functions
def generate_address():
    # Generates a mock cryptocurrency address
    return f"crypto-address-{len(users) + 1}"

def get_user_by_address(address):
    return users.get(address)

# Authentication Logic (simplified for demonstration purposes)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    address = generate_address()
    users[address] = {
        "name": data["name"],
        "balance": 0,
        "transactions": []
    }
    return jsonify({"address": address}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = get_user_by_address(data["address"])
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

# API Routes
@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    user = get_user_by_address(address)
    if user:
        return jsonify({"balance": user["balance"]}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/send', methods=['POST'])
def send():
    data = request.json
    sender = get_user_by_address(data["from"])
    receiver = get_user_by_address(data["to"])
    amount = data["amount"]

    if sender and receiver and sender["balance"] >= amount:
        sender["balance"] -= amount
        receiver["balance"] += amount
        transaction = {
            "from": data["from"],
            "to": data["to"],
            "amount": amount
        }
        transactions.append(transaction)
        sender["transactions"].append(transaction)
        receiver["transactions"].append(transaction)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Transaction failed"}), 400

@app.route('/history/<address>', methods=['GET'])
def get_history(address):
    user = get_user_by_address(address)
    if user:
        return jsonify({"transactions": user["transactions"]}), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5117')))
