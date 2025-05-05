"""
A Flask backend for a CRUD Inventory system.
Backend Port: 6157
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory "database" for inventory items
# Each item is a dict with keys: id, name, category, quantity, threshold (for stock alert)
inventory = []
next_id = 1  # auto-incrementing id

def get_item(item_id):
    """Utility to retrieve an item by its id."""
    return next((item for item in inventory if item['id'] == item_id), None)

# -----------------------------------------------------------
# CRUD API Routes for Inventory Items
# -----------------------------------------------------------

@app.route('/api/items', methods=['GET'])
def get_items():
    """
    GET /api/items
    Optional Query Params:
      - search: string to search in item name
      - category: filter by category name
    """
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '').lower()
    
    filtered_items = inventory
    if search:
        filtered_items = [item for item in filtered_items if search in item['name'].lower()]
    if category:
        filtered_items = [item for item in filtered_items if category == item['category'].lower()]

    return jsonify(filtered_items), 200

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_single_item(item_id):
    """GET /api/items/<item_id> returns a specific item."""
    item = get_item(item_id)
    if not item:
        abort(404, description="Item not found")
    return jsonify(item), 200

@app.route('/api/items', methods=['POST'])
def create_item():
    """POST /api/items creates a new inventory item."""
    global next_id
    data = request.get_json()
    # Basic validations
    if not data or 'name' not in data or 'category' not in data or 'quantity' not in data:
        abort(400, description="Missing required fields: name, category, quantity")
    
    try:
        quantity = int(data.get('quantity', 0))
        threshold = int(data.get('threshold', 0))
    except ValueError:
        abort(400, description="Quantity and threshold must be integer values.")
    
    new_item = {
        "id": next_id,
        "name": data['name'],
        "category": data['category'],
        "quantity": quantity,
        "threshold": threshold  # If quantity falls below threshold => alert in UI
    }
    inventory.append(new_item)
    next_id += 1
    return jsonify(new_item), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """PUT /api/items/<item_id> updates an existing inventory item."""
    item = get_item(item_id)
    if not item:
        abort(404, description="Item not found")
    
    data = request.get_json()
    # Update allowed fields if provided
    for field in ['name', 'category', 'quantity', 'threshold']:
        if field in data:
            if field in ['quantity', 'threshold']:
                try:
                    item[field] = int(data[field])
                except ValueError:
                    abort(400, description=f"{field} must be an integer")
            else:
                item[field] = data[field]
    
    return jsonify(item), 200

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """DELETE /api/items/<item_id> deletes an inventory item."""
    global inventory
    item = get_item(item_id)
    if not item:
        abort(404, description="Item not found")
    inventory = [it for it in inventory if it['id'] != item_id]
    return jsonify({"message": "Item deleted successfully"}), 200

# -----------------------------------------------------------
# Additional Routes for Multipage Routing (e.g., /login, /register)
# -----------------------------------------------------------

@app.route('/api/login', methods=['POST'])
def login():
    """A very simple login endpoint."""
    data = request.get_json()
    if not data or data.get("username") != "admin" or data.get("password") != "password":
        abort(401, description="Invalid credentials")
    # In production, token-based authentication would be used.
    return jsonify({"message": "Login successful", "user": "admin"}), 200

@app.route('/api/register', methods=['POST'])
def register():
    """A dummy register endpoint."""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        abort(400, description="Missing username or password")
    # In production, you would create a user record.
    return jsonify({"message": "Register successful"}), 201

# -----------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": error.description}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "message": error.description}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": error.description}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server Error", "message": "An internal error occurred"}), 500

if __name__ == '__main__':
    # Listen on all interfaces on port 6157 (backend port)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6157')), debug=False)
