# app.py

# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# In-Memory Data for Simplicity (Replace with Database in real apps)
transactions = []
goals = []

# 3. Utility Functions
def calculate_budget_summary():
    income = sum(txn['amount'] for txn in transactions if txn['type'] == 'income')
    expenses = sum(txn['amount'] for txn in transactions if txn['type'] == 'expense')
    balance = income - expenses
    return {"income": income, "expenses": expenses, "balance": balance}

def validate_transaction(data):
    required_fields = ["id", "amount", "category", "type", "description"]
    for field in required_fields:
        if field not in data:
            return False
    return True

# 4. API Endpoints

# a. Add Transaction (Income/Expense)
@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    data = request.json
    if validate_transaction(data):
        transactions.append(data)
        return jsonify({"message": "Transaction added successfully", "data": transactions}), 201
    return jsonify({"error": "Invalid data"}), 400

# b. Get Transactions
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    return jsonify({"data": transactions, "summary": calculate_budget_summary()}), 200

# c. Add Goal
@app.route('/api/goals', methods=['POST'])
def add_goal():
    data = request.json
    if "name" in data and "targetAmount" in data:
        goals.append(data)
        return jsonify({"message": "Goal added successfully", "data": goals}), 201
    return jsonify({"error": "Invalid data"}), 400

# d. Get Goals
@app.route('/api/goals', methods=['GET'])
def get_goals():
    return jsonify({"data": goals}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server Error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5285')))
