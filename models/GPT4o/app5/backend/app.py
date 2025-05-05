from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Simulated Database for Products and Cart (We could replace this with an actual database)
products = [
    {"id": 1, "name": "Laptop", "price": 1200.00, "stock": 5},
    {"id": 2, "name": "Smartphone", "price": 800.00, "stock": 8},
    {"id": 3, "name": "Headphones", "price": 150.00, "stock": 12},
]
cart = []


@app.route('/api/products', methods=['GET'])
def get_products():
    """API to fetch all products available in inventory."""
    return jsonify({"success": True, "products": products})


@app.route('/api/cart', methods=['GET'])
def get_cart():
    """API to fetch all items currently in the cart."""
    return jsonify({"success": True, "cart": cart})


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """API to add products to the cart."""
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    for product in products:
        if product["id"] == product_id:
            if product["stock"] >= quantity:
                # Add to cart
                cart_item = next((item for item in cart if item['id'] == product_id), None)
                if cart_item:
                    cart_item['quantity'] += quantity
                else:
                    cart.append({"id": product_id, "name": product["name"], "price": product["price"], "quantity": quantity})
                product["stock"] -= quantity
                return jsonify({"success": True, "message": "Product added to cart!"}), 200
            else:
                return jsonify({"success": False, "message": "Not enough stock available"}), 400

    return jsonify({"success": False, "message": "Product not found"}), 404


@app.route('/api/cart/checkout', methods=['POST'])
def checkout():
    """API to process cart checkout."""
    cart.clear()  # Clear out the cart after checkout
    return jsonify({"success": True, "message": "Checkout completed successfully!"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle unknown endpoints."""
    return jsonify({"success": False, "message": "Endpoint not found"}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5249)))
