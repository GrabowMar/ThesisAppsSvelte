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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
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
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# 4. Authentication Logic
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'error': 'Invalid username or password'}), 400

# 5. Utility Functions
def get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)

# 6. API Routes
@app.route('/posts', methods=['GET', 'POST'])
@jwt_required()
def posts():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Missing post content'}), 400

        new_post = Post(content=data['content'], user_id=get_current_user().id)
        db.session.add(new_post)
        db.session.commit()

        return jsonify({'message': 'Post created successfully', 'post_id': new_post.id}), 201

    elif request.method == 'GET':
        posts = Post.query.order_by(Post.created_at.desc()).all()
        return jsonify([{
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'author': post.author.username,
            'likes': len(post.likes),
            'comments': len(post.comments)
        } for post in posts])

@app.route('/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'GET':
        return jsonify({
            'id': post.id,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'author': post.author.username,
            'likes': len(post.likes),
            'comments': [{
                'id': comment.id,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'author': comment.author.username
            } for comment in post.comments]
        })

    elif request.method == 'PUT':
        if post.user_id != get_current_user().id:
            return jsonify({'error': 'You can only edit your own posts'}), 403

        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Missing post content'}), 400

        post.content = data['content']
        db.session.commit()

        return jsonify({'message': 'Post updated successfully'})

    elif request.method == 'DELETE':
        if post.user_id != get_current_user().id:
            return jsonify({'error': 'You can only delete your own posts'}), 403

        db.session.delete(post)
        db.session.commit()

        return jsonify({'message': 'Post deleted successfully'})

@app.route('/posts/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    user = get_current_user()

    if Like.query.filter_by(user_id=user.id, post_id=post_id).first():
        return jsonify({'error': 'You have already liked this post'}), 400

    new_like = Like(user_id=user.id, post_id=post_id)
    db.session.add(new_like)
    db.session.commit()

    return jsonify({'message': 'Post liked successfully'})

@app.route('/posts/<int:post_id>/comment', methods=['POST'])
@jwt_required()
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing comment content'}), 400

    new_comment = Comment(content=data['content'], user_id=get_current_user().id, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment added successfully', 'comment_id': new_comment.id})

@app.route('/search', methods=['GET'])
@jwt_required()
def search_posts():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    posts = Post.query.filter(Post.content.ilike(f'%{query}%')).order_by(Post.created_at.desc()).all()
    return jsonify([{
        'id': post.id,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'author': post.author.username,
        'likes': len(post.likes),
        'comments': len(post.comments)
    } for post in posts])

@app.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def profile():
    user = get_current_user()

    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'posts': len(user.posts)
        })

    elif request.method == 'PUT':
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'error': 'Missing username'}), 400

        if User.query.filter(User.id != user.id, User.username == data['username']).first():
            return jsonify({'error': 'Username already taken'}), 400

        user.username = data['username']
        db.session.commit()

        return jsonify({'message': 'Profile updated successfully'})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden'}), 403

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5499')))
