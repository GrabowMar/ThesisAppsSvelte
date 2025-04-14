# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# This is a simple in-memory storage for demonstration purposes
transactions = []
budgets = []
goals = []

# 4. Authentication Logic (if needed)
# Skipping for simplicity

# 5. Utility Functions
def generate_id(collection):
    return len(collection) + 1

# 6. API Routes
@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions_route():
    if request.method == 'POST':
        data = request.get_json()
        transaction = {
            'id': generate_id(transactions),
            'type': data['type'],
            'amount': data['amount'],
            'category': data['category'],
            'date': datetime.now().isoformat()
        }
        transactions.append(transaction)
        return jsonify(transaction), 201
    return jsonify(transactions), 200

@app.route('/api/budgets', methods=['GET', 'POST'])
def budgets_route():
    if request.method == 'POST':
        data = request.get_json()
        budget = {
            'id': generate_id(budgets),
            'category': data['category'],
            'amount': data['amount']
        }
        budgets.append(budget)
        return jsonify(budget), 201
    return jsonify(budgets), 200

@app.route('/api/goals', methods=['GET', 'POST'])
def goals_route():
    if request.method == 'POST':
        data = request.get_json()
        goal = {
            'id': generate_id(goals),
            'name': data['name'],
            'amount': data['amount'],
            'deadline': data['deadline']
        }
        goals.append(goal)
        return jsonify(goal), 201
    return jsonify(goals), 200

# 7. Error Handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5125')))
