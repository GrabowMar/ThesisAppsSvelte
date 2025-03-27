from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample in-memory database for inventory
inventory = [
    {"id": 1, "name": "Item A", "category": "Category 1", "stock": 10},
    {"id": 2, "name": "Item B", "category": "Category 2", "stock": 5},
]

current_id = 3  # Tracks the next available ID


# Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    """Fetch all items."""
    return jsonify(inventory), 200


@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Fetch a specific item by ID."""
    item = next((item for item in inventory if item["id"] == item_id), None)
    if item:
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item."""
    global current_id
    data = request.get_json()
    if not data or 'name' not in data or 'category' not in data or 'stock' not in data:
        return jsonify({"error": "Invalid payload"}), 400
    new_item = {
        "id": current_id,
        "name": data['name'],
        "category": data['category'],
        "stock": data['stock'],
    }
    inventory.append(new_item)
    current_id += 1
    return jsonify(new_item), 201


@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item's information."""
    data = request.get_json()
    item = next((item for item in inventory if item["id"] == item_id), None)
    if item:
        item.update({k: v for k, v in data.items() if k in item})
        return jsonify(item), 200
    return jsonify({"error": "Item not found"}), 404


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item by ID."""
    global inventory
    inventory = [item for item in inventory if item["id"] != item_id]
    return jsonify({"message": "Item deleted"}), 200


# Start server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5257)))
