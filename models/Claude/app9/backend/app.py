# app.py - Backend for Inventory Management System
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import os

# App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
CORS(app)
db = SQLAlchemy(app)

# Database Models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(200))
    items = db.relationship('Item', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    reorder_level = db.Column(db.Integer, default=5)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'quantity': self.quantity,
            'price': self.price,
            'reorder_level': self.reorder_level,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'low_stock': self.quantity <= self.reorder_level
        }

# Utility Functions
def create_initial_data():
    # Create some categories if none exist
    if Category.query.count() == 0:
        categories = [
            Category(name="Electronics", description="Electronic devices and accessories"),
            Category(name="Office Supplies", description="Stationery and office equipment"),
            Category(name="Furniture", description="Office and home furniture")
        ]
        db.session.add_all(categories)
        db.session.commit()
        
    # Create some initial items if none exist
    if Item.query.count() == 0:
        items = [
            Item(name="Laptop", description="Business laptop with 16GB RAM", quantity=10, price=1200.00, 
                 reorder_level=3, category_id=1),
            Item(name="Desk Chair", description="Ergonomic office chair", quantity=5, price=250.00, 
                 reorder_level=2, category_id=3),
            Item(name="Notepad", description="Legal pad, yellow, 50 sheets", quantity=100, price=3.99, 
                 reorder_level=20, category_id=2),
            Item(name="Monitor", description="27-inch 4K display", quantity=8, price=350.00, 
                 reorder_level=3, category_id=1),
            Item(name="Desk", description="Standing desk, adjustable height", quantity=4, price=400.00, 
                 reorder_level=2, category_id=3)
        ]
        db.session.add_all(items)
        db.session.commit()

# API Routes

# Home route
@app.route('/')
def home():
    return jsonify({"message": "Inventory Management API", "status": "active"})

# Items Routes
@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        # Get query parameters for filtering
        category_id = request.args.get('category_id', type=int)
        search_term = request.args.get('search', '')
        low_stock_only = request.args.get('low_stock', '').lower() == 'true'
        
        # Base query
        query = Item.query
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search_term:
            query = query.filter(Item.name.ilike(f'%{search_term}%') | 
                                 Item.description.ilike(f'%{search_term}%'))
        
        if low_stock_only:
            query = query.filter(Item.quantity <= Item.reorder_level)
        
        # Execute query and convert to dictionary
        items = [item.to_dict() for item in query.all()]
        
        return jsonify(items)
    except Exception as e:
        app.logger.error(f"Error fetching items: {str(e)}")
        return jsonify({"error": "Failed to fetch items"}), 500

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404
        return jsonify(item.to_dict())
    except Exception as e:
        app.logger.error(f"Error fetching item {item_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch item"}), 500

@app.route('/api/items', methods=['POST'])
def create_item():
    try:
        data = request.json
        
        if not data or not data.get('name'):
            return jsonify({"error": "Name is required"}), 400
            
        new_item = Item(
            name=data.get('name'),
            description=data.get('description', ''),
            quantity=data.get('quantity', 0),
            price=data.get('price', 0.0),
            reorder_level=data.get('reorder_level', 5),
            category_id=data.get('category_id')
        )
        
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error creating item: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error creating item: {str(e)}")
        return jsonify({"error": "Failed to create item"}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404
            
        data = request.json
        
        # Update fields if provided in the request
        if 'name' in data:
            item.name = data['name']
        if 'description' in data:
            item.description = data['description']
        if 'quantity' in data:
            item.quantity = data['quantity']
        if 'price' in data:
            item.price = data['price']
        if 'reorder_level' in data:
            item.reorder_level = data['reorder_level']
        if 'category_id' in data:
            item.category_id = data['category_id']
            
        db.session.commit()
        return jsonify(item.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error updating item {item_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error updating item {item_id}: {str(e)}")
        return jsonify({"error": "Failed to update item"}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        item = Item.query.get(item_id)
        if not item:
            return jsonify({"error": "Item not found"}), 404
            
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Item deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error deleting item {item_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error deleting item {item_id}: {str(e)}")
        return jsonify({"error": "Failed to delete item"}), 500

# Categories Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = [category.to_dict() for category in Category.query.all()]
        return jsonify(categories)
    except Exception as e:
        app.logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({"error": "Failed to fetch categories"}), 500

@app.route('/api/categories', methods=['POST'])
def create_category():
    try:
        data = request.json
        
        if not data or not data.get('name'):
            return jsonify({"error": "Name is required"}), 400
            
        new_category = Category(
            name=data.get('name'),
            description=data.get('description', '')
        )
        
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e):
            return jsonify({"error": "Category name already exists"}), 400
        app.logger.error(f"Database error creating category: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error creating category: {str(e)}")
        return jsonify({"error": "Failed to create category"}), 500

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404
            
        data = request.json
        
        # Update fields if provided
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
            
        db.session.commit()
        return jsonify(category.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        if 'UNIQUE constraint' in str(e):
            return jsonify({"error": "Category name already exists"}), 400
        app.logger.error(f"Database error updating category {category_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error updating category {category_id}: {str(e)}")
        return jsonify({"error": "Failed to update category"}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404
            
        # Check if any items use this category
        if Item.query.filter_by(category_id=category_id).first():
            return jsonify({"error": "Cannot delete category with associated items"}), 400
            
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": "Category deleted successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Database error deleting category {category_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.logger.error(f"Error deleting category {category_id}: {str(e)}")
        return jsonify({"error": "Failed to delete category"}), 500

# Dashboard Route - Get summary statistics
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    try:
        total_items = Item.query.count()
        total_categories = Category.query.count()
        total_quantity = db.session.query(db.func.sum(Item.quantity)).scalar() or 0
        low_stock_count = Item.query.filter(Item.quantity <= Item.reorder_level).count()
        
        # Get items with the highest stock value (price * quantity)
        top_items = db.session.query(
            Item.id, Item.name, 
            (Item.price * Item.quantity).label('value')
        ).order_by(db.desc('value')).limit(5).all()
        
        top_items_data = [
            {"id": item.id, "name": item.name, "value": round(item.value, 2)}
            for item in top_items
        ]
        
        # Categories with their item counts
        category_stats = db.session.query(
            Category.id, Category.name, db.func.count(Item.id).label('item_count')
        ).outerjoin(Item, Category.id == Item.category_id).group_by(Category.id).all()
        
        category_data = [
            {"id": cat.id, "name": cat.name, "item_count": cat.item_count}
            for cat in category_stats
        ]
        
        return jsonify({
            "total_items": total_items,
            "total_categories": total_categories,
            "total_quantity": total_quantity,
            "low_stock_count": low_stock_count,
            "top_items": top_items_data,
            "category_stats": category_data
        })
    except Exception as e:
        app.logger.error(f"Error fetching dashboard data: {str(e)}")
        return jsonify({"error": "Failed to fetch dashboard data"}), 500

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

with app.app_context():
    # Create tables and initial data
    db.create_all()
    create_initial_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5337')), debug=False)