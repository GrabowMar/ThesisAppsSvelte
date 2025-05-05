# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. Database Models
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    alert_level = db.Column(db.Integer, nullable=False)

# 4. Utility Functions
def item_to_dict(item):
    return {
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'stock': item.stock,
        'alert_level': item.alert_level
    }

# 5. API Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([item_to_dict(item) for item in items])

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    new_item = Item(
        name=data['name'],
        category=data['category'],
        stock=data['stock'],
        alert_level=data['alert_level']
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(item_to_dict(new_item)), 201

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item_to_dict(item))

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get_or_404(item_id)
    data = request.get_json()
    item.name = data['name']
    item.category = data['category']
    item.stock = data['stock']
    item.alert_level = data['alert_level']
    db.session.commit()
    return jsonify(item_to_dict(item))

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return '', 204

# 6. Error Handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error="Internal server error"), 500

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5097')))
