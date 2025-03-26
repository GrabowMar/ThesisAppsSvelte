# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Comment('{self.content}', '{self.date_posted}')"

# 4. Authentication Logic (if needed)
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    new_user = User(username=username, email=email, password=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return jsonify({'message': 'Login successful!'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# 5. Utility Functions
def get_user_id(username):
    user = User.query.filter_by(username=username).first()
    return user.id

# 6. API Routes
@app.route('/post', methods=['POST'])
def create_post():
    title = request.json['title']
    content = request.json['content']
    user_id = get_user_id(request.json['username'])
    new_post = Post(title=title, content=content, user_id=user_id)
    db.session.add(new_post)
    db.session.commit()
    return jsonify({'message': 'Post created successfully!'}), 201

@app.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)
    return jsonify({'title': post.title, 'content': post.content}), 200

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    content = request.json['content']
    user_id = get_user_id(request.json['username'])
    new_comment = Comment(content=content, post_id=post_id, user_id=user_id)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'Comment created successfully!'}), 201

@app.route('/post/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    # Implement like logic here
    return jsonify({'message': 'Post liked successfully!'}), 201

@app.route('/post/<int:post_id>/search', methods=['POST'])
def search_post(post_id):
    query = request.json['query']
    # Implement search logic here
    return jsonify({'message': 'Search results'}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5019')))
