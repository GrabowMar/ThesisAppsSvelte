# app/backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample Inventory Data (replace with a database in a real application)
inventory = [
    {"id": 1, "name": "Laptop", "category": "Electronics", "stock": 5, "price": 1200},
    {"id": 2, "name": "Notebook", "category": "Stationery", "stock": 50, "price": 2},
    {"id": 3, "name": "Mouse", "category": "Electronics", "stock": 20, "price": 25}
]

next_id = 4  # To keep track of the next available ID


# Utility Functions
def find_item(item_id):
    for item in inventory:
        if item['id'] == item_id:
            return item
    return None


# API Routes

# Get all items
@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify(inventory)


# Get a specific item
@app.route('/api/inventory/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = find_item(item_id)
    if item:
        return jsonify(item)
    return jsonify({"message": "Item not found"}), 404


# Create a new item
@app.route('/api/inventory', methods=['POST'])
def create_item():
    global next_id
    data = request.get_json()
    if not all(key in data for key in ('name', 'category', 'stock', 'price')):
        return jsonify({"message": "Missing required fields"}), 400

    new_item = {
        "id": next_id,
        "name": data['name'],
        "category": data['category'],
        "stock": data['stock'],
        "price": data['price']
    }
    inventory.append(new_item)
    next_id += 1
    return jsonify(new_item), 201


# Update an existing item
@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = find_item(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    data = request.get_json()
    if 'name' in data:
        item['name'] = data['name']
    if 'category' in data:
        item['category'] = data['category']
    if 'stock' in data:
        item['stock'] = data['stock']
    if 'price' in data:
        item['price'] = data['price']

    return jsonify(item)


# Delete an item
@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global inventory
    item = find_item(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    inventory = [i for i in inventory if i['id'] != item_id]  # Create a new list excluding the item
    return jsonify({"message": "Item deleted"})


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({"message": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5417')), debug=True)