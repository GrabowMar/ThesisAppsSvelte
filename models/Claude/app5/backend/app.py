# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')  # Change in production

# 3. Database Models (using simple JSON storage for this template)
# In a production app, you would use a proper database

# Initialize data store
def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "products": [
                {"id": "1", "name": "Premium Headphones", "price": 129.99, "image": "headphones.jpg", "stock": 15, "description": "High-quality audio headphones with noise cancellation."},
                {"id": "2", "name": "Wireless Mouse", "price": 49.99, "image": "mouse.jpg", "stock": 20, "description": "Ergonomic wireless mouse with long battery life."},
                {"id": "3", "name": "Mechanical Keyboard", "price": 89.99, "image": "keyboard.jpg", "stock": 10, "description": "RGB mechanical keyboard with customizable switches."},
                {"id": "4", "name": "4K Monitor", "price": 299.99, "image": "monitor.jpg", "stock": 8, "description": "27-inch 4K Ultra HD monitor with wide color gamut."},
                {"id": "5", "name": "Laptop Stand", "price": 35.99, "image": "laptop-stand.jpg", "stock": 25, "description": "Adjustable aluminum laptop stand for ergonomic positioning."},
                {"id": "6", "name": "USB-C Hub", "price": 59.99, "image": "usb-hub.jpg", "stock": 18, "description": "7-in-1 USB-C hub with HDMI, USB 3.0, and card readers."}
            ],
            "users": [],
            "orders": []
        }

def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=2)

# 4. Authentication Logic
@app.route('/api/register', methods=['POST'])
def register():
    data = load_data()
    user_data = request.json
    
    # Validate input
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in user_data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if user exists
    if any(u['email'] == user_data['email'] for u in data['users']):
        return jsonify({"error": "User with this email already exists"}), 400
    
    # Create new user
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data['username'],
        "email": user_data['email'],
        "password": generate_password_hash(user_data['password']),
        "cart": []
    }
    
    data['users'].append(new_user)
    save_data(data)
    
    # Set session
    session_user = dict(new_user)
    del session_user['password']
    session['user'] = session_user
    
    return jsonify({"message": "Registration successful", "user": session_user}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = load_data()
    user_data = request.json
    
    # Validate input
    if 'email' not in user_data or 'password' not in user_data:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user
    user = next((u for u in data['users'] if u['email'] == user_data['email']), None)
    if not user or not check_password_hash(user['password'], user_data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Set session
    session_user = dict(user)
    del session_user['password']
    session['user'] = session_user
    
    return jsonify({"message": "Login successful", "user": session_user})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user' in session:
        return jsonify({"authenticated": True, "user": session['user']})
    return jsonify({"authenticated": False})

# 5. Utility Functions
def get_user_by_id(user_id, data):
    return next((u for u in data['users'] if u['id'] == user_id), None)

def update_product_stock(product_id, quantity, data):
    product = next((p for p in data['products'] if p['id'] == product_id), None)
    if product and product['stock'] >= quantity:
        product['stock'] -= quantity
        return True
    return False

# 6. API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    data = load_data()
    return jsonify(data['products'])

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    data = load_data()
    product = next((p for p in data['products'] if p['id'] == product_id), None)
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product)

@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = load_data()
    user = get_user_by_id(session['user']['id'], data)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Enhance cart with product details
    cart_with_details = []
    for item in user['cart']:
        product = next((p for p in data['products'] if p['id'] == item['product_id']), None)
        if product:
            cart_with_details.append({
                "product_id": item['product_id'],
                "quantity": item['quantity'],
                "name": product['name'],
                "price": product['price'],
                "image": product['image'],
                "subtotal": product['price'] * item['quantity']
            })
    
    return jsonify({
        "items": cart_with_details,
        "total": sum(item['subtotal'] for item in cart_with_details)
    })

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    cart_item = request.json
    
    # Validate input
    if 'product_id' not in cart_item or 'quantity' not in cart_item:
        return jsonify({"error": "Product ID and quantity are required"}), 400
    
    if cart_item['quantity'] <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400
    
    data = load_data()
    
    # Validate product
    product = next((p for p in data['products'] if p['id'] == cart_item['product_id']), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product['stock'] < cart_item['quantity']:
        return jsonify({"error": "Not enough stock available"}), 400
    
    # Update user cart
    user_id = session['user']['id']
    user = get_user_by_id(user_id, data)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if product already in cart
    existing_item = next((item for item in user['cart'] if item['product_id'] == cart_item['product_id']), None)
    
    if existing_item:
        if product['stock'] < (existing_item['quantity'] + cart_item['quantity']):
            return jsonify({"error": "Not enough stock available"}), 400
        existing_item['quantity'] += cart_item['quantity']
    else:
        user['cart'].append({
            "product_id": cart_item['product_id'],
            "quantity": cart_item['quantity']
        })
    
    save_data(data)
    session['user']['cart'] = user['cart']
    
    return jsonify({"message": "Item added to cart successfully"})

@app.route('/api/cart/<product_id>', methods=['PUT'])
def update_cart_item(product_id):
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    update_data = request.json
    
    # Validate input
    if 'quantity' not in update_data:
        return jsonify({"error": "Quantity is required"}), 400
    
    quantity = update_data['quantity']
    
    if quantity <= 0:
        return jsonify({"error": "Quantity must be positive"}), 400
    
    data = load_data()
    
    # Validate product
    product = next((p for p in data['products'] if p['id'] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    if product['stock'] < quantity:
        return jsonify({"error": "Not enough stock available"}), 400
    
    # Update user cart
    user_id = session['user']['id']
    user = get_user_by_id(user_id, data)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if product in cart
    cart_item = next((item for item in user['cart'] if item['product_id'] == product_id), None)
    
    if not cart_item:
        return jsonify({"error": "Product not found in cart"}), 404
    
    cart_item['quantity'] = quantity
    save_data(data)
    session['user']['cart'] = user['cart']
    
    return jsonify({"message": "Cart updated successfully"})

@app.route('/api/cart/<product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = load_data()
    
    # Update user cart
    user_id = session['user']['id']
    user = get_user_by_id(user_id, data)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Remove item from cart
    user['cart'] = [item for item in user['cart'] if item['product_id'] != product_id]
    save_data(data)
    session['user']['cart'] = user['cart']
    
    return jsonify({"message": "Item removed from cart successfully"})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    checkout_data = request.json
    
    # Validate input
    required_fields = ['address', 'city', 'zip', 'payment_method']
    for field in required_fields:
        if field not in checkout_data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    data = load_data()
    
    user_id = session['user']['id']
    user = get_user_by_id(user_id, data)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not user['cart']:
        return jsonify({"error": "Cart is empty"}), 400
    
    # Calculate order total and verify stock
    order_items = []
    total = 0
    
    for cart_item in user['cart']:
        product = next((p for p in data['products'] if p['id'] == cart_item['product_id']), None)
        
        if not product:
            return jsonify({"error": f"Product {cart_item['product_id']} not found"}), 404
        
        if product['stock'] < cart_item['quantity']:
            return jsonify({"error": f"Not enough stock for {product['name']}"}), 400
        
        item_total = product['price'] * cart_item['quantity']
        total += item_total
        
        order_items.append({
            "product_id": cart_item['product_id'],
            "name": product['name'],
            "price": product['price'],
            "quantity": cart_item['quantity'],
            "subtotal": item_total
        })
    
    # Create order
    order = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "items": order_items,
        "total": total,
        "status": "processing",
        "shipping_address": {
            "address": checkout_data['address'],
            "city": checkout_data['city'],
            "zip": checkout_data['zip']
        },
        "payment_method": checkout_data['payment_method'],
        "created_at": datetime.now().isoformat()
    }
    
    # Update product stock
    for item in user['cart']:
        update_product_stock(item['product_id'], item['quantity'], data)
    
    # Clear user cart
    user['cart'] = []
    
    # Save order
    data['orders'].append(order)
    save_data(data)
    session['user']['cart'] = []
    
    return jsonify({"message": "Order placed successfully", "order": order})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = load_data()
    user_id = session['user']['id']
    
    user_orders = [order for order in data['orders'] if order['user_id'] == user_id]
    return jsonify(user_orders)

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    if 'user' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = load_data()
    user_id = session['user']['id']
    
    order = next((o for o in data['orders'] if o['id'] == order_id and o['user_id'] == user_id), None)
    
    if not order:
        return jsonify({"error": "Order not found"}), 404
    
    return jsonify(order)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5329')), debug=False)
