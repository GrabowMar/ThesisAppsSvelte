# 1. Imports Section
from flask import Flask, jsonify, request, session, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import jwt
import os
import uuid
import markdown

# 2. App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_extremely_secret')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt_secret_key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

CORS(app, supports_credentials=True)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, username, email, password):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

class Category(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    posts = db.relationship('Post', backref='category', lazy=True)
    
    def __init__(self, name, description=""):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description

class Post(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('category.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, title, content, user_id, category_id):
        self.id = str(uuid.uuid4())
        self.title = title
        self.content = content
        self.user_id = user_id
        self.category_id = category_id

class Comment(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.String(36), db.ForeignKey('post.id'), nullable=False)
    
    def __init__(self, content, user_id, post_id):
        self.id = str(uuid.uuid4())
        self.content = content
        self.user_id = user_id
        self.post_id = post_id

# 4. Authentication Logic
def generate_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(
        payload,
        app.config.get('JWT_SECRET_KEY'),
        algorithm='HS256'
    )

def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
            
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        try:
            data = jwt.decode(token, app.config.get('JWT_SECRET_KEY'), algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['sub']).first()
            
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except (jwt.InvalidTokenError, Exception) as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
            
        return f(current_user, *args, **kwargs)
        
    decorated.__name__ = f.__name__
    return decorated

# 5. Utility Functions
def serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    }

def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description
    }

def serialize_post(post, include_html=True):
    data = {
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'author': serialize_user(post.author),
        'category': serialize_category(post.category),
        'comments_count': len(post.comments)
    }
    
    if include_html:
        data['html_content'] = markdown.markdown(post.content)
        
    return data

def serialize_comment(comment):
    return {
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat(),
        'author': serialize_user(comment.author)
    }

# 6. API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Service is running'})

# Auth Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check for existing user
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409
    
    # Create new user
    try:
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        
        token = generate_token(new_user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': serialize_user(new_user),
            'token': token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    try:
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not bcrypt.check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': serialize_user(user),
            'token': token
        })
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({'user': serialize_user(current_user)})

# Category Routes
@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify({
        'categories': [serialize_category(category) for category in categories]
    })

@app.route('/api/categories', methods=['POST'])
@token_required
def create_category(current_user):
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Category name is required'}), 400
    
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Category already exists'}), 409
    
    try:
        new_category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': serialize_category(new_category)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

# Post Routes
@app.route('/api/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category_id')
    
    query = Post.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    posts_pagination = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page)
    
    posts = [serialize_post(post, include_html=False) for post in posts_pagination.items]
    
    return jsonify({
        'posts': posts,
        'total': posts_pagination.total,
        'pages': posts_pagination.pages,
        'current_page': page
    })

@app.route('/api/posts/<string:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    return jsonify({
        'post': serialize_post(post)
    })

@app.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content') or not data.get('category_id'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if category exists
    category = Category.query.get(data['category_id'])
    if not category:
        return jsonify({'message': 'Category not found'}), 404
    
    try:
        new_post = Post(
            title=data['title'],
            content=data['content'],
            user_id=current_user.id,
            category_id=data['category_id']
        )
        db.session.add(new_post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': serialize_post(new_post)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/posts/<string:post_id>', methods=['PUT'])
@token_required
def update_post(current_user, post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    if post.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized to edit this post'}), 403
    
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    try:
        if data.get('title'):
            post.title = data['title']
        
        if data.get('content'):
            post.content = data['content']
        
        if data.get('category_id'):
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({'message': 'Category not found'}), 404
            post.category_id = data['category_id']
        
        post.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Post updated successfully',
            'post': serialize_post(post)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/posts/<string:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user, post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    if post.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized to delete this post'}), 403
    
    try:
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

# Comment Routes
@app.route('/api/posts/<string:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()
    
    return jsonify({
        'comments': [serialize_comment(comment) for comment in comments]
    })

@app.route('/api/posts/<string:post_id>/comments', methods=['POST'])
@token_required
def create_comment(current_user, post_id):
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': 'Comment content is required'}), 400
    
    try:
        new_comment = Comment(
            content=data['content'],
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': serialize_comment(new_comment)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/comments/<string:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, comment_id):
    comment = Comment.query.get(comment_id)
    
    if not comment:
        return jsonify({'message': 'Comment not found'}), 404
    
    if comment.user_id != current_user.id:
        return jsonify({'message': 'Unauthorized to delete this comment'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

# 7. Initialize Database and Seed Data
@app.before_first_request
def initialize_db():
    db.create_all()
    
    # Create default categories if none exist
    if Category.query.count() == 0:
        default_categories = [
            Category('Technology', 'Tech-related posts'),
            Category('Travel', 'Travel experiences and tips'),
            Category('Food', 'Recipes and restaurant reviews'),
            Category('Lifestyle', 'Posts about daily life and wellness'),
            Category('Other', 'Miscellaneous topics')
        ]
        
        for category in default_categories:
            db.session.add(category)
        
        db.session.commit()

# 8. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request'}), 400

@app.errorhandler(500)
def server_error(error):
    db.session.rollback()
    return jsonify({'message': 'Internal server error'}), 500

# Initialize app
with app.app_context():
    db.create_all()
    # Create default categories if none exist
    if Category.query.count() == 0:
        default_categories = [
            Category('Technology', 'Tech-related posts'),
            Category('Travel', 'Travel experiences and tips'),
            Category('Food', 'Recipes and restaurant reviews'),
            Category('Lifestyle', 'Posts about daily life and wellness'),
            Category('Other', 'Miscellaneous topics')
        ]
        
        for category in default_categories:
            db.session.add(category)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5327')))
