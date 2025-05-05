# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# For simplicity, we will use a dictionary to store products and orders
products = {
    "1": {"name": "Product 1", "price": 10.99},
    "2": {"name": "Product 2", "price": 9.99},
    "3": {"name": "Product 3", "price": 12.99},
}

orders = {}

# 4. Authentication Logic (if needed)
# No authentication is implemented for simplicity

# 5. Utility Functions
def generate_order_id():
    return str(uuid.uuid4())

# 6. API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(list(products.values()))

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    if product_id not in products:
        return jsonify({"error": "Product not found"}), 404
    if 'cart' not in orders:
        orders['cart'] = []
    orders['cart'].append(product_id)
    return jsonify({"message": "Product added to cart"})

@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'cart' not in orders:
        return jsonify({"cart": []})
    cart = []
    for product_id in orders['cart']:
        cart.append(products[product_id])
    return jsonify({"cart": cart})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    order_id = generate_order_id()
    orders[order_id] = orders['cart']
    del orders['cart']
    return jsonify({"order_id": order_id, "order": orders[order_id]})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5009')))
