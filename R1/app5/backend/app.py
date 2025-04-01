from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
from uuid import uuid4
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["http://localhost:6069"], supports_credentials=True)

# In-memory data storage
products = [
    {"id": 1, "name": "Laptop", "price": 999.99, "stock": 10},
    {"id": 2, "name": "Phone", "price": 699.99, "stock": 15},
    {"id": 3, "name": "Headphones", "price": 149.99, "stock": 20}
]

carts = {}
orders = {}

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify(products)

@app.route('/api/cart', methods=['GET', 'POST'])
def manage_cart():
    cart_id = request.cookies.get('cart_id')
    
    if request.method == 'GET':
        cart = carts.get(cart_id, [])
        return jsonify(cart)
    
    if request.method == 'POST':
        data = request.get_json()
        product_id = data['product_id']
        quantity = data.get('quantity', 1)
        
        product = next((p for p in products if p['id'] == product_id), None)
        if not product or product['stock'] < quantity:
            return jsonify({"error": "Product unavailable"}), 400
            
        if not cart_id or cart_id not in carts:
            cart_id = str(uuid4())
            carts[cart_id] = []
            
        existing_item = next((i for i in carts[cart_id] if i['product_id'] == product_id), None)
        if existing_item:
            existing_item['quantity'] += quantity
        else:
            carts[cart_id].append({"product_id": product_id, "quantity": quantity})
        
        resp = make_response(jsonify(carts[cart_id]))
        resp.set_cookie('cart_id', cart_id, max_age=86400*7)  # 1 week
        return resp

@app.route('/api/checkout', methods=['POST'])
def checkout():
    cart_id = request.cookies.get('cart_id')
    if not cart_id or cart_id not in carts:
        return jsonify({"error": "Cart not found"}), 400
        
    data = request.get_json()
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "Missing customer information"}), 400
    
    # Process order
    order_id = str(uuid4())
    order = {
        "id": order_id,
        "customer": data,
        "items": carts[cart_id],
        "total": sum(item['quantity'] * next(p['price'] for p in products if p['id'] == item['product_id']) 
                   for item in carts[cart_id]),
        "date": datetime.now().isoformat()
    }
    
    # Update stock
    for item in carts[cart_id]:
        product = next(p for p in products if p['id'] == item['product_id'])
        product['stock'] -= item['quantity']
    
    orders[order_id] = order
    del carts[cart_id]
    
    resp = make_response(jsonify(order))
    resp.delete_cookie('cart_id')
    return resp

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order)

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5569')))
