# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# 3. Mock Database (Replace with a real database in production)
inventory = [
    {"id": 1, "name": "Laptop", "category": "Electronics", "stock": 10},
    {"id": 2, "name": "Chair", "category": "Furniture", "stock": 5},
]

# 4. Utility Functions
def find_item(item_id):
    return next((item for item in inventory if item["id"] == item_id), None)

# 5. API Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    return jsonify(inventory)

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    return jsonify(item)

@app.route('/api/items', methods=['POST'])
def create_item():
    if not request.json or not 'name' in request.json:
        abort(400, description="Invalid input: 'name' is required")
    item = {
        "id": len(inventory) + 1,
        "name": request.json['name'],
        "category": request.json.get('category', 'Uncategorized'),
        "stock": request.json.get('stock', 0),
    }
    inventory.append(item)
    return jsonify(item), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    if 'name' in request.json:
        item['name'] = request.json['name']
    if 'category' in request.json:
        item['category'] = request.json['category']
    if 'stock' in request.json:
        item['stock'] = request.json['stock']
    return jsonify(item)

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    inventory.remove(item)
    return jsonify({"message": "Item deleted successfully"})

# 6. Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5177)
