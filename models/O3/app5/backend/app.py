"""
E-Commerce Cart Application - Backend (Flask)
Port: 6149
Dependencies (see requirements.txt):
  - Flask
  - flask-cors
This file implements in-memory product listing, cart management, checkout,
and orders history endpoints.
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory "database" data stores
products = [
    {
        "id": 1,
        "name": "Product 1",
        "price": 19.99,
        "inventory": 10,
        "description": "Awesome product 1."
    },
    {
        "id": 2,
        "name": "Product 2",
        "price": 29.99,
        "inventory": 5,
        "description": "Great product 2."
    },
    {
        "id": 3,
        "name": "Product 3",
        "price": 9.99,
        "inventory": 20,
        "description": "Useful product 3."
    },
]

# For simplicity, we assume a single-session cart and orders storage.
cart = {}   # key: product_id, value: quantity in cart
orders = [] # list of order records

def find_product(product_id):
    """Helper to lookup a product by id."""
    return next((p for p in products if p["id"] == product_id), None)

# ---------------------------
# API Routes
# ---------------------------

@app.route('/api/products', methods=['GET'])
def get_products():
    """Return the list of available products."""
    return jsonify({"success": True, "products": products}), 200

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Return the current cart summary (with product details)."""
    cart_items = []
    for pid, qty in cart.items():
        product = find_product(pid)
        if product:
            item = product.copy()
            item["quantity"] = qty
            cart_items.append(item)
    return jsonify({"success": True, "cart": cart_items}), 200

@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    """
    Add or update an item in the cart.
    Request json must include:
      - product_id: integer
      - quantity: integer (> 0)
    """
    data = request.get_json()
    if not data or "product_id" not in data or "quantity" not in data:
        return jsonify({"success": False, "message": "Product ID and quantity are required."}), 400

    product_id = data["product_id"]
    quantity = data["quantity"]

    product = find_product(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404

    if quantity <= 0:
        return jsonify({"success": False, "message": "Quantity must be greater than zero."}), 400

    current_in_cart = cart.get(product_id, 0)
    if product["inventory"] < current_in_cart + quantity:
        return jsonify({"success": False, "message": "Not enough inventory available."}), 400

    cart[product_id] = current_in_cart + quantity
    return jsonify({"success": True, "message": "Product added to cart.", "cart": cart}), 200

@app.route('/api/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    """Remove an item from the cart."""
    if product_id in cart:
        del cart[product_id]
        return jsonify({"success": True, "message": "Product removed from cart.", "cart": cart}), 200
    else:
        return jsonify({"success": False, "message": "Product not in cart."}), 404

@app.route('/api/checkout', methods=['POST'])
def checkout():
    """
    Process the checkout.
    - Validates inventory for all items.
    - Deducts ordered quantity.
    - Creates an order record.
    - Clears the cart.
    """
    if not cart:
        return jsonify({"success": False, "message": "Cart is empty."}), 400

    order_total = 0.0
    order_items = []

    for pid, qty in cart.items():
        product = find_product(pid)
        if product:
            if product["inventory"] < qty:
                return jsonify({"success": False, "message": f"Insufficient inventory for product {product['name']}."}), 400
            order_total += qty * product["price"]
            order_items.append({
                "id": product["id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": qty
            })
            product["inventory"] -= qty

    order = {
        "order_id": len(orders) + 1,
        "items": order_items,
        "total": round(order_total, 2)
    }
    orders.append(order)
    cart.clear()
    return jsonify({"success": True, "message": "Checkout successful.", "order": order}), 200

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Return the list of customer's orders."""
    return jsonify({"success": True, "orders": orders}), 200

# ---------------------------
# Error Handlers
# ---------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Resource not found."}), 404

# ---------------------------
# App Runner
# ---------------------------
if __name__ == '__main__':
    # Running on port 6149 (default override via PORT env variable is supported)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6149')), debug=False)
