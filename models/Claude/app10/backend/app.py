# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
from sqlalchemy import desc, or_

# 2. App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # In production, use env variable
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
CORS(app)

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='author', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='user', lazy=True, cascade="all, delete-orphan")

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True, cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='post', lazy=True, cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Ensure a user can only like a post once
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)

# 4. Authentication Logic
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    
    # Validate input data
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    # Generate token
    token = create_access_token(identity=new_user.id)
    
    return jsonify({
        'token': token,
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'bio': new_user.bio
        }
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    
    # Validate input data
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({'error': 'Missing email or password'}), 400
    
    # Find the user
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists and password is correct
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = create_access_token(identity=user.id)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'bio': user.bio
        }
    }), 200

# 5. Profile Management
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'bio': user.bio,
        'created_at': user.created_at.isoformat()
    }), 200

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    data = request.json
    
    # Update fields if provided
    if 'bio' in data:
        user.bio = data['bio']
    
    if 'email' in data:
        # Check if email is taken by another user
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Email already in use'}), 409
        user.email = data['email']
    
    # Optional password update
    if 'password' in data and data['password']:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'bio': user.bio
    }), 200

@app.route('/api/profile/<username>', methods=['GET'])
def get_user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's posts
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    
    posts_data = []
    for post in posts:
        like_count = Like.query.filter_by(post_id=post.id).count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        posts_data.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'like_count': like_count,
            'comment_count': comment_count
        })
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'bio': user.bio,
            'created_at': user.created_at.isoformat()
        },
        'posts': posts_data
    }), 200

# 6. Post CRUD Operations
@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Post content is required'}), 400
    
    if len(data['content']) > 280:
        return jsonify({'error': 'Post content exceeds maximum length (280 characters)'}), 400
    
    new_post = Post(content=data['content'], user_id=user_id)
    db.session.add(new_post)
    db.session.commit()
    
    return jsonify({
        'id': new_post.id,
        'content': new_post.content,
        'created_at': new_post.created_at.isoformat(),
        'user_id': new_post.user_id,
        'author': {
            'username': new_post.author.username
        }
    }), 201

@app.route('/api/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts_query = Post.query.order_by(desc(Post.created_at))
    posts_paginate = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = []
    for post in posts_paginate.items:
        user = User.query.get(post.user_id)
        like_count = Like.query.filter_by(post_id=post.id).count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        # Current user like status (if authenticated)
        user_liked = False
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                current_user_id = get_jwt_identity()
                user_liked = Like.query.filter_by(post_id=post.id, user_id=current_user_id).first() is not None
            except:
                # If token is invalid or expired, just pass
                pass
        
        result.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'author': {
                'id': user.id,
                'username': user.username
            },
            'like_count': like_count,
            'comment_count': comment_count,
            'user_liked': user_liked
        })
    
    return jsonify({
        'posts': result,
        'page': page,
        'per_page': per_page,
        'total': posts_paginate.total,
        'pages': posts_paginate.pages
    }), 200

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = User.query.get(post.user_id)
    
    # Get likes and comments
    likes = Like.query.filter_by(post_id=post.id).count()
    comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.created_at.desc()).all()
    
    comments_data = []
    for comment in comments:
        comment_author = User.query.get(comment.user_id)
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'author': {
                'id': comment_author.id,
                'username': comment_author.username
            }
        })
    
    return jsonify({
        'id': post.id,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'author': {
            'id': user.id,
            'username': user.username
        },
        'like_count': likes,
        'comments': comments_data
    }), 200

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    # Verify post ownership
    if post.user_id != user_id:
        return jsonify({'error': 'You can only update your own posts'}), 403
    
    data = request.json
    
    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Post content is required'}), 400
    
    if len(data['content']) > 280:
        return jsonify({'error': 'Post content exceeds maximum length (280 characters)'}), 400
    
    post.content = data['content']
    db.session.commit()
    
    return jsonify({
        'id': post.id,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'user_id': post.user_id
    }), 200

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = get_jwt_identity()
    post = Post.query.get_or_404(post_id)
    
    # Verify post ownership
    if post.user_id != user_id:
        return jsonify({'error': 'You can only delete your own posts'}), 403
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted successfully'}), 200

# 7. Post Interactions (Likes/Comments)
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    user_id = get_jwt_identity()
    
    # Check if post exists
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        return jsonify({'error': 'You already liked this post'}), 400
    
    # Create new like
    new_like = Like(user_id=user_id, post_id=post_id)
    db.session.add(new_like)
    db.session.commit()
    
    # Get updated like count
    like_count = Like.query.filter_by(post_id=post_id).count()
    
    return jsonify({'message': 'Post liked successfully', 'like_count': like_count}), 200

@app.route('/api/posts/<int:post_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_post(post_id):
    user_id = get_jwt_identity()
    
    # Check if post exists
    Post.query.get_or_404(post_id)
    
    # Find and remove the like
    like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if not like:
        return jsonify({'error': 'You have not liked this post'}), 400
    
    db.session.delete(like)
    db.session.commit()
    
    # Get updated like count
    like_count = Like.query.filter_by(post_id=post_id).count()
    
    return jsonify({'message': 'Post unliked successfully', 'like_count': like_count}), 200

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    user_id = get_jwt_identity()
    data = request.json
    
    # Check if post exists
    post = Post.query.get_or_404(post_id)
    
    if not data or 'content' not in data or not data['content'].strip():
        return jsonify({'error': 'Comment content is required'}), 400
    
    if len(data['content']) > 140:
        return jsonify({'error': 'Comment content exceeds maximum length (140 characters)'}), 400
    
    # Create comment
    new_comment = Comment(
        content=data['content'],
        user_id=user_id,
        post_id=post_id
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    user = User.query.get(user_id)
    
    return jsonify({
        'id': new_comment.id,
        'content': new_comment.content,
        'created_at': new_comment.created_at.isoformat(),
        'author': {
            'id': user.id,
            'username': user.username
        }
    }), 201

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    # Verify comment ownership
    if comment.user_id != user_id:
        return jsonify({'error': 'You can only delete your own comments'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted successfully'}), 200

# 8. Post Search
@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    # Search in post content and user names
    posts_query = db.session.query(Post).join(User).filter(
        or_(
            Post.content.ilike(f'%{query}%'),
            User.username.ilike(f'%{query}%')
        )
    ).order_by(Post.created_at.desc())
    
    posts_paginate = posts_query.paginate(page=page, per_page=per_page, error_out=False)
    
    result = []
    for post in posts_paginate.items:
        user = User.query.get(post.user_id)
        like_count = Like.query.filter_by(post_id=post.id).count()
        comment_count = Comment.query.filter_by(post_id=post.id).count()
        
        result.append({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'author': {
                'id': user.id,
                'username': user.username
            },
            'like_count': like_count,
            'comment_count': comment_count
        })
    
    return jsonify({
        'posts': result,
        'page': page,
        'per_page': per_page,
        'total': posts_paginate.total,
        'pages': posts_paginate.pages,
        'query': query
    }), 200

# 9. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5339')))
