from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Sample data
products = [
    {"id": 1, "name": "Product 1", "price": 10, "stock": 10},
    {"id": 2, "name": "Product 2", "price": 20, "stock": 5},
    {"id": 3, "name": "Product 3", "price": 30, "stock": 2},
]

cart = []


@app.route("/")
def index():
    return "E-Commerce Backend Running"


@app.route("/api/products", methods=["GET"])
def get_products():
    return jsonify(products)


@app.route("/api/cart", methods=["GET"])
def get_cart():
    return jsonify(cart)


@app.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    product_id = data.get("productId")
    quantity = data.get("quantity", 1)

    product = next((p for p in products if p["id"] == product_id), None)
    if not product or product["stock"] < quantity:
        abort(400, "Product not found or insufficient stock")

    product_in_cart = next((item for item in cart if item["id"] == product_id), None)
    if product_in_cart:
        product_in_cart["quantity"] += quantity
    else:
        cart.append({"id": product_id, "name": product["name"], "price": product["price"], "quantity": quantity})

    product["stock"] -= quantity
    return jsonify(cart)


@app.route("/api/cart/remove/<int:product_id>", methods=["DELETE"])
def remove_from_cart(product_id):
    product_in_cart = next((item for item in cart if item["id"] == product_id), None)
    if not product_in_cart:
        abort(404, "Product not found in cart")

    product = next((p for p in products if p["id"] == product_id), None)
    if product:
        product["stock"] += product_in_cart["quantity"]

    cart[:] = [item for item in cart if item["id"] != product_id]
    return jsonify(cart)


@app.route("/api/checkout", methods=["POST"])
def checkout():
    global cart
    if not cart:
        abort(400, "Cart is empty")

    # Clear the cart
    cart = []
    return jsonify({"message": "Checkout successful"})


if __name__ == "__main__":
    app.run(port=5169, debug=True)
