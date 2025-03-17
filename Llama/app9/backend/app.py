from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample in-memory data store (replace with a database in a real application)
items = [
    {"id": 1, "name": "Item 1", "category": "Category 1", "stock_level": 10},
    {"id": 2, "name": "Item 2", "category": "Category 2", "stock_level": 20},
    {"id": 3, "name": "Item 3", "category": "Category 1", "stock_level": 30},
]

# API endpoint to get all items
@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(items)

# API endpoint to get a single item by id
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if item is None:
        return jsonify({"message": "Item not found"}), 404
    return jsonify(item)

# API endpoint to create a new item
@app.route('/items', methods=['POST'])
def create_item():
    new_item = {
        "id": len(items) + 1,
        "name": request.json["name"],
        "category": request.json["category"],
        "stock_level": request.json["stock_level"],
    }
    items.append(new_item)
    return jsonify(new_item), 201

# API endpoint to update an existing item
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if item is None:
        return jsonify({"message": "Item not found"}), 404
    item["name"] = request.json.get("name", item["name"])
    item["category"] = request.json.get("category", item["category"])
    item["stock_level"] = request.json.get("stock_level", item["stock_level"])
    return jsonify(item)

# API endpoint to delete an item
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = next((item for item in items if item["id"] == item_id), None)
    if item is None:
        return jsonify({"message": "Item not found"}), 404
    items.remove(item)
    return jsonify({"message": "Item deleted"})

if __name__ == '__main__':
    app.run(port=5017)
