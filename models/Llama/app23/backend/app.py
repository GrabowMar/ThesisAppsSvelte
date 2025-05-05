# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (using in-memory dictionary for simplicity)
data = {
    "transactions": [],
    "budgets": [],
    "goals": []
}

# 4. Authentication Logic (simple token-based authentication)
users = {"user1": "password1"}
auth_token = "secret_token"

# 5. Utility Functions
def validate_auth_token(token):
    return token == auth_token

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username in users and users[username] == password:
        return jsonify({"token": auth_token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions():
    token = request.headers.get('Authorization')
    if not validate_auth_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'GET':
        return jsonify(data["transactions"])
    
    transaction = {
        "id": len(data["transactions"]) + 1,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "amount": request.json.get('amount'),
        "category": request.json.get('category'),
        "type": request.json.get('type')
    }
    data["transactions"].append(transaction)
    return jsonify(transaction), 201

@app.route('/api/budgets', methods=['GET', 'POST'])
def budgets():
    token = request.headers.get('Authorization')
    if not validate_auth_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'GET':
        return jsonify(data["budgets"])
    
    budget = {
        "id": len(data["budgets"]) + 1,
        "category": request.json.get('category'),
        "limit": request.json.get('limit')
    }
    data["budgets"].append(budget)
    return jsonify(budget), 201

@app.route('/api/goals', methods=['GET', 'POST'])
def goals():
    token = request.headers.get('Authorization')
    if not validate_auth_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == 'GET':
        return jsonify(data["goals"])
    
    goal = {
        "id": len(data["goals"]) + 1,
        "target": request.json.get('target'),
        "progress": 0
    }
    data["goals"].append(goal)
    return jsonify(goal), 201

@app.route('/api/reports', methods=['GET'])
def reports():
    token = request.headers.get('Authorization')
    if not validate_auth_token(token):
        return jsonify({"error": "Unauthorized"}), 401
    
    income = sum(t["amount"] for t in data["transactions"] if t["type"] == "income")
    expenses = sum(t["amount"] for t in data["transactions"] if t["type"] == "expense")
    return jsonify({"income": income, "expenses": expenses})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5045')))
