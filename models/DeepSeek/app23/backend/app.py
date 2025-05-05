# 1. Imports Section
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from datetime import datetime
import os
import json
from uuid import uuid4

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)

# 3. Database Models (simplified in-memory storage)
transactions = []
budgets = []
goals = []
users = [{
    "id": "demo",
    "username": "demo",
    "password": "demo",
    "email": "demo@example.com"
}]
categories = [
    "Food", "Transportation", "Housing", "Utilities", 
    "Healthcare", "Entertainment", "Education", "Savings", 
    "Debt", "Other"
]

# 4. Authentication Logic
def authenticate_user(username, password):
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

# 5. Utility Functions
def calculate_balance():
    income = sum(t['amount'] for t in transactions if t['type'] == 'income')
    expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    return income - expenses

def get_monthly_summary():
    monthly_data = {}
    for transaction in transactions:
        date = datetime.strptime(transaction['date'], '%Y-%m-%d')
        month_year = f"{date.year}-{date.month:02d}"
        
        if month_year not in monthly_data:
            monthly_data[month_year] = {
                'income': 0,
                'expenses': 0,
                'balance': 0
            }
        
        if transaction['type'] == 'income':
            monthly_data[month_year]['income'] += transaction['amount']
        else:
            monthly_data[month_year]['expenses'] += transaction['amount']
        
        monthly_data[month_year]['balance'] = monthly_data[month_year]['income'] - monthly_data[month_year]['expenses']
    
    return monthly_data

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = authenticate_user(data['username'], data['password'])
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if any(u['username'] == data['username'] for u in users):
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    new_user = {
        'id': str(uuid4()),
        'username': data['username'],
        'password': data['password'],
        'email': data['email']
    }
    users.append(new_user)
    return jsonify({'success': True, 'user': new_user})

@app.route('/api/transactions', methods=['GET', 'POST'])
def handle_transactions():
    if request.method == 'GET':
        return jsonify(transactions)
    elif request.method == 'POST':
        data = request.get_json()
        new_transaction = {
            'id': str(uuid4()),
            'type': data['type'],
            'amount': float(data['amount']),
            'category': data['category'],
            'description': data['description'],
            'date': data['date']
        }
        transactions.append(new_transaction)
        return jsonify(new_transaction), 201

@app.route('/api/transactions/<transaction_id>', methods=['DELETE', 'PUT'])
def handle_single_transaction(transaction_id):
    transaction = next((t for t in transactions if t['id'] == transaction_id), None)
    if not transaction:
        return jsonify({'success': False, 'message': 'Transaction not found'}), 404
    
    if request.method == 'DELETE':
        transactions.remove(transaction)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.get_json()
        transaction.update({
            'type': data['type'],
            'amount': float(data['amount']),
            'category': data['category'],
            'description': data['description'],
            'date': data['date']
        })
        return jsonify(transaction)

@app.route('/api/summary', methods=['GET'])
def get_summary():
    return jsonify({
        'balance': calculate_balance(),
        'income': sum(t['amount'] for t in transactions if t['type'] == 'income'),
        'expenses': sum(t['amount'] for t in transactions if t['type'] == 'expense'),
        'monthly_summary': get_monthly_summary()
    })

@app.route('/api/budgets', methods=['GET', 'POST'])
def handle_budgets():
    if request.method == 'GET':
        return jsonify(budgets)
    elif request.method == 'POST':
        data = request.get_json()
        new_budget = {
            'id': str(uuid4()),
            'category': data['category'],
            'amount': float(data['amount']),
            'month': data['month']
        }
        budgets.append(new_budget)
        return jsonify(new_budget), 201

@app.route('/api/budgets/<budget_id>', methods=['DELETE', 'PUT'])
def handle_single_budget(budget_id):
    budget = next((b for b in budgets if b['id'] == budget_id), None)
    if not budget:
        return jsonify({'success': False, 'message': 'Budget not found'}), 404
    
    if request.method == 'DELETE':
        budgets.remove(budget)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.get_json()
        budget.update({
            'category': data['category'],
            'amount': float(data['amount']),
            'month': data['month']
        })
        return jsonify(budget)

@app.route('/api/goals', methods=['GET', 'POST'])
def handle_goals():
    if request.method == 'GET':
        return jsonify(goals)
    elif request.method == 'POST':
        data = request.get_json()
        new_goal = {
            'id': str(uuid4()),
            'name': data['name'],
            'target_amount': float(data['target_amount']),
            'current_amount': float(data.get('current_amount', 0)),
            'target_date': data['target_date'],
            'status': data.get('status', 'in_progress')
        }
        goals.append(new_goal)
        return jsonify(new_goal), 201

@app.route('/api/goals/<goal_id>', methods=['DELETE', 'PUT'])
def handle_single_goal(goal_id):
    goal = next((g for g in goals if g['id'] == goal_id), None)
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    if request.method == 'DELETE':
        goals.remove(goal)
        return jsonify({'success': True})
    elif request.method == 'PUT':
        data = request.get_json()
        goal.update({
            'name': data['name'],
            'target_amount': float(data['target_amount']),
            'current_amount': float(data['current_amount']),
            'target_date': data['target_date'],
            'status': data['status']
        })
        return jsonify(goal)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(categories)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Internal server error'}), 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5205')))
