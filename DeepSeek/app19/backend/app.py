from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock data for demonstration purposes
user = {
    "balance": 1000.00,
    "address": "0x1234567890abcdef",
    "transactions": [
        {"id": 1, "type": "send", "amount": 100.00, "to": "0x0987654321fedcba", "timestamp": "2023-10-01T12:00:00"},
        {"id": 2, "type": "receive", "amount": 200.00, "from": "0x13579acegikmoqs", "timestamp": "2023-10-02T14:30:00"}
    ]
}

@app.route("/")
def index():
    return render_template("index.html")  # Serve the React app

@app.route("/api/balance", methods=["GET"])
def get_balance():
    """Fetch the user's balance."""
    return jsonify({"balance": user["balance"]})

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    """Fetch the user's transaction history."""
    return jsonify({"transactions": user["transactions"]})

@app.route("/api/send", methods=["POST"])
def send_transaction():
    """Handle a send transaction request."""
    data = request.get_json()
    amount = data.get("amount")
    to_address = data.get("to")

    if not amount or not to_address:
        return jsonify({"error": "Missing required fields"}), 400

    if amount > user["balance"]:
        return jsonify({"error": "Insufficient funds"}), 400

    user["balance"] -= amount
    user["transactions"].append({
        "id": len(user["transactions"]) + 1,
        "type": "send",
        "amount": amount,
        "to": to_address,
        "timestamp": "2023-10-03T10:00:00"  # Mock timestamp
    })
    return jsonify({"message": "Transaction successful", "balance": user["balance"]})

@app.route("/api/address", methods=["GET"])
def get_address():
    """Fetch the user's wallet address."""
    return jsonify({"address": user["address"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5197, debug=True)
