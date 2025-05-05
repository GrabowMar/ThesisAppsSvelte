from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory storage for demonstration purposes
users = {}
products = [
    {"id": 1, "name": "Laptop", "price": 999.99, "quantity": 10},
    {"id": 2, "name": "Smartphone", "price": 499.99, "quantity": 20},
    {"id": 3, "name": "Headphones", "price": 99.99, "quantity": 30},
]
carts = {}

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or token != 'Bearer correct_token':
            abort(401)
        return f(*args, **kwargs)
    return decorated

# User registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if data.get('username') in users:
        return jsonify({"error": "Username already exists"}), 400
    hashed_password = generate_password_hash(data.get('password'))
    users[data.get('username')] = hashed_password
    return jsonify({"message": "User registered successfully"}), 201

# User login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = users.get(data.get('username'))
    if user and check_password_hash(user, data.get('password')):
        return jsonify({"token": "correct_token"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# Get products
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products), 200

# Add to cart
@app.route('/api/cart', methods=['POST'])
@require_auth
def add_to_cart():
    data = request.json
    username = request.headers.get('X-User')
    if username not in carts:
        carts[username] = []
    product = next((p for p in products if p['id'] == data['productId']), None)
    if product and product['quantity'] > 0:
        product['quantity'] -= 1
        carts[username].append({
            "productId": data['productId'],
            "name": product['name'],
            "price": product['price'],
            "quantity": data['quantity']
        })
        return jsonify({"message": "Product added to cart"}), 200
    return jsonify({"error": "Product not available"}), 400

# Get cart
@app.route('/api/cart', methods=['GET'])
@require_auth
def get_cart():
    username = request.headers.get('X-User')
    if username in carts:
        return jsonify(carts[username]), 200
    return jsonify([]), 200

# Checkout
@app.route('/api/checkout', methods=['POST'])
@require_auth
def checkout():
    username = request.headers.get('X-User')
    if username in carts:
        total = sum(item['price'] * item['quantity'] for item in carts[username])
        carts[username] = []
        return jsonify({"total": total, "message": "Order placed successfully"}), 200
    return jsonify({"error": "Cart is empty"}), 400

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5989')))
