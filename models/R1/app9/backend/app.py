# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Database
items = [
    {
        "id": str(uuid.uuid4()),
        "name": "Sample Laptop",
        "category": "Electronics",
        "stock": 5,
        "min_stock": 10
    }
]

# 4. Utility Functions
def find_item(item_id):
    return next((item for item in items if item["id"] == item_id), None)

# 5. API Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    search = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    filtered = items.copy()
    
    if category != 'all':
        filtered = [i for i in filtered if i['category'] == category]
    
    if search:
        filtered = [i for i in filtered if search.lower() in i['name'].lower()]
    
    return jsonify(filtered)

@app.route('/api/items/low-stock', methods=['GET'])
def get_low_stock():
    low_stock = [i for i in items if i['stock'] < i['min_stock']]
    return jsonify(low_stock)

@app.route('/api/items', methods=['POST'])
def create_item():
    if not request.json or 'name' not in request.json:
        abort(400, description="Missing required fields")
    
    new_item = {
        "id": str(uuid.uuid4()),
        "name": request.json['name'],
        "category": request.json.get('category', 'Uncategorized'),
        "stock": request.json.get('stock', 0),
        "min_stock": request.json.get('min_stock', 0)
    }
    items.append(new_item)
    return jsonify(new_item), 201

@app.route('/api/items/<string:item_id>', methods=['PUT'])
def update_item(item_id):
    item = find_item(item_id)
    if not item:
        abort(404)
    
    data = request.json
    item['name'] = data.get('name', item['name'])
    item['category'] = data.get('category', item['category'])
    item['stock'] = data.get('stock', item['stock'])
    item['min_stock'] = data.get('min_stock', item['min_stock'])
    
    return jsonify(item)

@app.route('/api/items/<string:item_id>', methods=['DELETE'])
def delete_item(item_id):
    global items
    item = find_item(item_id)
    if not item:
        abort(404)
    
    items = [i for i in items if i['id'] != item_id]
    return jsonify({'result': True})

# 6. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5577')))
