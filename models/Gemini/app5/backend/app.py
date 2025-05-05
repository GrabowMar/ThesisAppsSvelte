# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Data - using a JSON file for simplicity.  In a real app, would use a database.
DATA_FILE = 'products.json'

# Load products from JSON file
def load_products():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []  # Return an empty list if the file doesn't exist
    except json.JSONDecodeError:
        return []  # Handle corrupted JSON data

# Save products to JSON file
def save_products(products):
    with open(DATA_FILE, 'w') as f:
        json.dump(products, f, indent=4)

products = load_products() # initialize

# Example Products (if products.json doesn't exist or is empty)
if not products:
  products = [
    {"id": 1, "name": "Product A", "price": 20, "inventory": 100, "image": "https://via.placeholder.com/150"},
    {"id": 2, "name": "Product B", "price": 30, "inventory": 50, "image": "https://via.placeholder.com/150"},
    {"id": 3, "name": "Product C", "price": 40, "inventory": 75, "image": "https://via.placeholder.com/150"}
  ]
  save_products(products)


# 4. API Routes

@app.route('/api/products', methods=['GET'])
def get_products():
    """Returns all products."""
    return jsonify(products)


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Returns a specific product by ID."""
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    return jsonify({'message': 'Product not found'}), 404


@app.route('/api/cart', methods=['POST'])
def update_cart():
    """Updates the cart (simulated) by adjusting product inventory."""
    data = request.get_json()
    product_id = data.get('productId')
    quantity = data.get('quantity')
    action = data.get('action')  # 'add' or 'remove'

    if not all([product_id, quantity, action]):
        return jsonify({'message': 'Missing parameters'}), 400

    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    if action == 'add':
        if product['inventory'] >= quantity:
            product['inventory'] -= quantity
            save_products(products)
            return jsonify({'message': f'Added {quantity} of {product["name"]} to cart', 'inventory': product['inventory']})
        else:
            return jsonify({'message': 'Not enough inventory'}), 400
    elif action == 'remove':
        product['inventory'] += quantity
        save_products(products)
        return jsonify({'message': f'Removed {quantity} of {product["name"]} from cart', 'inventory': product['inventory']})
    else:
        return jsonify({'message': 'Invalid action'}), 400


@app.route('/api/checkout', methods=['POST'])
def checkout():
    """Simulates a checkout process."""
    # In a real application, this would involve payment processing,
    # order creation, and other relevant steps.
    data = request.get_json()
    cart_items = data.get('cartItems')  # Expecting a list of {productId: , quantity: }
    if not cart_items:
        return jsonify({'message': 'No items in cart'}), 400

    total_price = 0
    for item in cart_items:
        product_id = item.get('productId')
        quantity = item.get('quantity')

        product = next((p for p in products if p['id'] == product_id), None)
        if not product:
            return jsonify({'message': f'Product with id {product_id} not found'}), 404
        total_price += product['price'] * quantity

    return jsonify({'message': 'Checkout successful', 'total': total_price})


# 5. Error Handlers (Example)
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404


# 6. Server Startup
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5409')), debug=True)
