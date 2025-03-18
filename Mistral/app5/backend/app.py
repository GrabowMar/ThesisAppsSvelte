from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample data
products = [
    {"id": 1, "name": "Product 1", "price": 10.0, "quantity": 100},
    {"id": 2, "name": "Product 2", "price": 20.0, "quantity": 200},
    {"id": 3, "name": "Product 3", "price": 30.0, "quantity": 300},
]

cart = []
orders = []

# Routes
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/cart', methods=['GET'])
def get_cart():
    return jsonify(cart)

@app.route('/cart', methods=['POST'])
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    product = next((p for p in products if p['id'] == product_id), None)
    if product and product['quantity'] >= quantity:
        cart.append({"product_id": product_id, "quantity": quantity})
        product['quantity'] -= quantity
        return make_response(jsonify({"message": "Product added to cart"}), 200)
    else:
        return make_response(jsonify({"message": "Product not available or insufficient quantity"}), 400)

@app.route('/checkout', methods=['POST'])
def checkout():
    global cart
    if not cart:
        return make_response(jsonify({"message": "Cart is empty"}), 400)

    order = {"products": cart, "total": sum(p['quantity'] * next(prod['price'] for prod in products if prod['id'] == p['product_id']) for p in cart)}
    orders.append(order)
    cart = []
    return jsonify(order)

@app.route('/orders', methods=['GET'])
def get_orders():
    return jsonify(orders)

if __name__ == '__main__':
    app.run(port=5089)
