from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# In-Memory Database (Replace with a real database in production)
inventory = [
    {"id": 1, "name": "Item 1", "category": "Electronics", "stock": 10, "alert": False},
    {"id": 2, "name": "Item 2", "category": "Clothing", "stock": 5, "alert": True},
]

# Helper function to find an item by ID
def find_item(item_id):
    return next((item for item in inventory if item["id"] == item_id), None)

# Route to get all items
@app.route("/api/items", methods=["GET"])
def get_items():
    return jsonify(inventory)

# Route to get a single item by ID
@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    return jsonify(item)

# Route to add a new item
@app.route("/api/items", methods=["POST"])
def add_item():
    if not request.json or not "name" in request.json:
        abort(400, description="Invalid request: Missing required fields")
    new_item = {
        "id": len(inventory) + 1,
        "name": request.json["name"],
        "category": request.json.get("category", "Uncategorized"),
        "stock": request.json.get("stock", 0),
        "alert": request.json.get("stock", 0) <= 5,  # Alert if stock is 5 or less
    }
    inventory.append(new_item)
    return jsonify(new_item), 201

# Route to update an item by ID
@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    if not request.json:
        abort(400, description="Invalid request: No data provided")
    item["name"] = request.json.get("name", item["name"])
    item["category"] = request.json.get("category", item["category"])
    item["stock"] = request.json.get("stock", item["stock"])
    item["alert"] = item["stock"] <= 5  # Recalculate alert
    return jsonify(item)

# Route to delete an item by ID
@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, description="Item not found")
    inventory.remove(item)
    return jsonify({"message": "Item deleted"}), 200

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

# Error handler for 400
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5177)
