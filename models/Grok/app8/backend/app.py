# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from datetime import datetime, timedelta

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 4. Authentication Logic
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Username or email already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password, email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid username or password'}), 401

# 5. Utility Functions
def paginate_results(results, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return results[start:end]

# 6. API Routes
@app.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])

@app.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Category already exists'}), 400

    new_category = Category(name=data['name'])
    db.session.add(new_category)
    db.session.commit()

    return jsonify({'id': new_category.id, 'name': new_category.name}), 201

@app.route('/threads', methods=['GET'])
def get_threads():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    category_id = request.args.get('category_id')

    query = Thread.query

    if category_id:
        query = query.filter_by(category_id=category_id)

    if sort_by in ['created_at', 'updated_at']:
        query = query.order_by(getattr(Thread, sort_by).desc() if sort_order == 'desc' else getattr(Thread, sort_by).asc())

    threads = query.all()
    paginated_threads = paginate_results(threads, page, per_page)

    return jsonify({
        'threads': [
            {
                'id': t.id,
                'title': t.title,
                'content': t.content,
                'user_id': t.user_id,
                'category_id': t.category_id,
                'created_at': t.created_at.isoformat(),
                'updated_at': t.updated_at.isoformat()
            } for t in paginated_threads
        ],
        'total': len(threads),
        'page': page,
        'per_page': per_page
    })

@app.route('/threads', methods=['POST'])
@jwt_required()
def create_thread():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data or 'category_id' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    user_id = get_jwt_identity()
    new_thread = Thread(title=data['title'], content=data['content'], user_id=user_id, category_id=data['category_id'])
    db.session.add(new_thread)
    db.session.commit()

    return jsonify({'id': new_thread.id, 'title': new_thread.title}), 201

@app.route('/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    return jsonify({
        'id': thread.id,
        'title': thread.title,
        'content': thread.content,
        'user_id': thread.user_id,
        'category_id': thread.category_id,
        'created_at': thread.created_at.isoformat(),
        'updated_at': thread.updated_at.isoformat()
    })

@app.route('/threads/<int:thread_id>/comments', methods=['GET'])
def get_comments(thread_id):
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')

    query = Comment.query.filter_by(thread_id=thread_id)

    if sort_by in ['created_at', 'updated_at']:
        query = query.order_by(getattr(Comment, sort_by).desc() if sort_order == 'desc' else getattr(Comment, sort_by).asc())

    comments = query.all()
    paginated_comments = paginate_results(comments, page, per_page)

    return jsonify({
        'comments': [
            {
                'id': c.id,
                'content': c.content,
                'user_id': c.user_id,
                'thread_id': c.thread_id,
                'created_at': c.created_at.isoformat(),
                'updated_at': c.updated_at.isoformat()
            } for c in paginated_comments
        ],
        'total': len(comments),
        'page': page,
        'per_page': per_page
    })

@app.route('/threads/<int:thread_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(thread_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

    user_id = get_jwt_identity()
    new_comment = Comment(content=data['content'], user_id=user_id, thread_id=thread_id)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'id': new_comment.id, 'content': new_comment.content}), 201

@app.route('/search', methods=['GET'])
def search_threads():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    results = Thread.query.filter(Thread.title.ilike(f'%{query}%') | Thread.content.ilike(f'%{query}%')).all()
    paginated_results = paginate_results(results, page, per_page)

    return jsonify({
        'threads': [
            {
                'id': t.id,
                'title': t.title,
                'content': t.content,
                'user_id': t.user_id,
                'category_id': t.category_id,
                'created_at': t.created_at.isoformat(),
                'updated_at': t.updated_at.isoformat()
            } for t in paginated_results
        ],
        'total': len(results),
        'page': page,
        'per_page': per_page
    })

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request'}), 400

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5495')))
