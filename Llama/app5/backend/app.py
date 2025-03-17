from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample in-memory data store for products and cart
products = [
    {"id": 1, "name": "Product 1", "price": 9.99},
    {"id": 2, "name": "Product 2", "price": 19.99},
    {"id": 3, "name": "Product 3", "price": 29.99},
]

cart = []

# Backend API routes
@app.route("/products", methods=["GET"])
def get_products():
    """Returns a list of available products."""
    return jsonify(products)

@app.route("/cart", methods=["GET"])
def get_cart():
    """Returns the current cart contents."""
    return jsonify(cart)

@app.route("/cart", methods=["POST"])
def add_to_cart():
    """Adds a product to the cart."""
    product_id = request.json["product_id"]
    for product in products:
        if product["id"] == product_id:
            cart.append(product)
            return jsonify({"message": "Product added to cart"}), 201
    return jsonify({"message": "Product not found"}), 404

@app.route("/cart", methods=["DELETE"])
def remove_from_cart():
    """Removes a product from the cart."""
    product_id = request.json["product_id"]
    for i, product in enumerate(cart):
        if product["id"] == product_id:
            del cart[i]
            return jsonify({"message": "Product removed from cart"}), 200
    return jsonify({"message": "Product not found in cart"}), 404

@app.route("/checkout", methods=["POST"])
def checkout():
    """Simulates a checkout process."""
    # Calculate total cost
    total_cost = sum(product["price"] for product in cart)
    # Clear cart
    cart.clear()
    return jsonify({"message": "Checkout successful", "total_cost": total_cost}), 200

if __name__ == "__main__":
    app.run(port=5009)
