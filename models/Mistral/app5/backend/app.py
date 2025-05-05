from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Example product data
products = [
    {"id": 1, "name": "Product 1", "price": 10.0, "stock": 100},
    {"id": 2, "name": "Product 2", "price": 20.0, "stock": 50},
    # Add more products as needed
]

# Example cart data
cart = []

# Utility function to find a product by ID
def find_product(product_id):
    return next((product for product in products if product["id"] == product_id), None)

# API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/cart', methods=['GET'])
def get_cart():
    return jsonify(cart)

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    product = find_product(product_id)
    if product and product["stock"] >= quantity:
        cart_item = next((item for item in cart if item["product_id"] == product_id), None)
        if cart_item:
            cart_item["quantity"] += quantity
        else:
            cart.append({"product_id": product_id, "quantity": quantity})
        product["stock"] -= quantity
        return jsonify({"message": "Item added to cart"}), 200
    else:
        return jsonify({"message": "Product not available or insufficient stock"}), 400

@app.route('/api/checkout', methods=['POST'])
def checkout():
    global cart
    order_summary = cart.copy()
    cart = []
    return jsonify(order_summary)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5089')))
