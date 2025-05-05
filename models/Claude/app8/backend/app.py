# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta

# 2. App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    threads = db.relationship('Thread', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    threads = db.relationship('Thread', backref='category', lazy=True)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    comments = db.relationship('Comment', backref='thread', lazy=True, cascade="all, delete-orphan")
    views = db.Column(db.Integer, default=0)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)

# 4. Utility Functions
def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'created_at': user.created_at.isoformat()
    }

def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'thread_count': len(category.threads)
    }

def serialize_thread(thread, include_comments=False):
    data = {
        'id': thread.id,
        'title': thread.title,
        'content': thread.content,
        'created_at': thread.created_at.isoformat(),
        'updated_at': thread.updated_at.isoformat(),
        'category_id': thread.category_id,
        'category_name': thread.category.name,
        'author': serialize_user(thread.author),
        'comment_count': len(thread.comments),
        'views': thread.views
    }
    
    if include_comments:
        data['comments'] = [serialize_comment(comment) for comment in thread.comments]
        
    return data

def serialize_comment(comment):
    return {
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'updated_at': comment.updated_at.isoformat(),
        'author': serialize_user(comment.author)
    }

# Initialize database with some categories
@app.before_first_request
def initialize_db():
    db.create_all()
    
    # Add default categories if none exist
    if Category.query.count() == 0:
        categories = [
            {"name": "General", "description": "General discussions"},
            {"name": "Technology", "description": "Tech related discussions"},
            {"name": "Sports", "description": "Sports related discussions"},
            {"name": "Entertainment", "description": "Movies, TV, music, etc."},
            {"name": "Science", "description": "Scientific discussions"}
        ]
        
        for cat in categories:
            category = Category(name=cat["name"], description=cat["description"])
            db.session.add(category)
        
        db.session.commit()

# 5. Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
        
    hashed_password = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        access_token = create_access_token(identity=new_user.id)
        return jsonify({
            "message": "User registered successfully",
            "user": serialize_user(new_user),
            "token": access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid username or password"}), 401
        
    access_token = create_access_token(identity=user.id)
    return jsonify({
        "message": "Login successful",
        "user": serialize_user(user),
        "token": access_token
    }), 200

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify(serialize_user(user)), 200

# 6. Category Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([serialize_category(category) for category in categories]), 200

# 7. Thread Routes
@app.route('/api/threads', methods=['GET'])
def get_threads():
    # Support for filtering, sorting, and pagination
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'new')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Thread.query
    
    # Apply category filter if provided
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply search if provided
    if search:
        query = query.filter(Thread.title.ilike(f'%{search}%') | Thread.content.ilike(f'%{search}%'))
    
    # Apply sorting
    if sort_by == 'new':
        query = query.order_by(Thread.created_at.desc())
    elif sort_by == 'top':
        query = query.order_by(Thread.views.desc())
    elif sort_by == 'comments':
        # This is a simplified approach - in production, you might want to optimize this
        threads = query.all()
        threads.sort(key=lambda t: len(t.comments), reverse=True)
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_threads = threads[start:end]
        
        return jsonify({
            'threads': [serialize_thread(thread) for thread in paginated_threads],
            'total': len(threads),
            'pages': (len(threads) + per_page - 1) // per_page,
            'current_page': page
        }), 200
    
    # Apply pagination for database-sorted queries
    paginated = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'threads': [serialize_thread(thread) for thread in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    }), 200

@app.route('/api/threads', methods=['POST'])
@jwt_required()
def create_thread():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or not data.get('title') or not data.get('content') or not data.get('category_id'):
        return jsonify({"error": "Title, content and category are required"}), 400
    
    # Verify category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({"error": "Category not found"}), 404
    
    # Create new thread
    new_thread = Thread(
        title=data['title'],
        content=data['content'],
        user_id=user_id,
        category_id=data['category_id']
    )
    
    try:
        db.session.add(new_thread)
        db.session.commit()
        return jsonify({
            "message": "Thread created successfully",
            "thread": serialize_thread(new_thread)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = Thread.query.get(thread_id)
    
    if not thread:
        return jsonify({"error": "Thread not found"}), 404
    
    # Increment view count
    thread.views += 1
    db.session.commit()
    
    return jsonify(serialize_thread(thread, include_comments=True)), 200

@app.route('/api/threads/<int:thread_id>', methods=['PUT'])
@jwt_required()
def update_thread(thread_id):
    user_id = get_jwt_identity()
    thread = Thread.query.get(thread_id)
    
    if not thread:
        return jsonify({"error": "Thread not found"}), 404
    
    if thread.user_id != user_id:
        return jsonify({"error": "Unauthorized to update this thread"}), 403
    
    data = request.json
    
    if 'title' in data:
        thread.title = data['title']
    if 'content' in data:
        thread.content = data['content']
    if 'category_id' in data:
        # Verify category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({"error": "Category not found"}), 404
        thread.category_id = data['category_id']
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Thread updated successfully",
            "thread": serialize_thread(thread)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/threads/<int:thread_id>', methods=['DELETE'])
@jwt_required()
def delete_thread(thread_id):
    user_id = get_jwt_identity()
    thread = Thread.query.get(thread_id)
    
    if not thread:
        return jsonify({"error": "Thread not found"}), 404
    
    if thread.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this thread"}), 403
    
    try:
        db.session.delete(thread)
        db.session.commit()
        return jsonify({"message": "Thread deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 8. Comment Routes
@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(thread_id):
    user_id = get_jwt_identity()
    thread = Thread.query.get(thread_id)
    
    if not thread:
        return jsonify({"error": "Thread not found"}), 404
    
    data = request.json
    
    if not data or not data.get('content'):
        return jsonify({"error": "Comment content is required"}), 400
    
    new_comment = Comment(
        content=data['content'],
        user_id=user_id,
        thread_id=thread_id
    )
    
    try:
        db.session.add(new_comment)
        db.session.commit()
        return jsonify({
            "message": "Comment added successfully",
            "comment": serialize_comment(new_comment)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
def update_comment(comment_id):
    user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({"error": "Comment not found"}), 404
    
    if comment.user_id != user_id:
        return jsonify({"error": "Unauthorized to update this comment"}), 403
    
    data = request.json
    
    if not data or not data.get('content'):
        return jsonify({"error": "Comment content is required"}), 400
    
    comment.content = data['content']
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Comment updated successfully",
            "comment": serialize_comment(comment)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({"error": "Comment not found"}), 404
    
    if comment.user_id != user_id:
        return jsonify({"error": "Unauthorized to delete this comment"}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({"message": "Comment deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 9. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5335')), debug=True)