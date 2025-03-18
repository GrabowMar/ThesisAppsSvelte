from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///microblog.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    likes = db.relationship('Like', backref='user', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 400

    user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    login_user(user)
    return jsonify({"message": "Logged in successfully"}), 200

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    return jsonify([{"id": post.id, "content": post.content, "author": post.author.username} for post in posts]), 200

@app.route('/posts', methods=['POST'])
@login_required
def create_post():
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({"message": "Content is required"}), 400

    post = Post(content=content, user_id=current_user.id)
    db.session.add(post)
    db.session.commit()
    return jsonify({"message": "Post created successfully"}), 201

@app.route('/posts/<int:id>', methods=['PUT'])
@login_required
def update_post(id):
    post = Post.query.get_or_404(id)

    if post.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    post.content = data.get('content', post.content)
    db.session.commit()
    return jsonify({"message": "Post updated successfully"}), 200

@app.route('/posts/<int:id>', methods=['DELETE'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)

    if post.user_id != current_user.id:
        return jsonify({"message": "Unauthorized"}), 403

    db.session.delete(post)
    db.session.commit()
    return jsonify({"message": "Post deleted successfully"}), 200

@app.route('/posts/search', methods=['GET'])
def search_posts():
    query = request.args.get('query')
    posts = Post.query.filter(Post.content.contains(query)).all()
    return jsonify([{"id": post.id, "content": post.content, "author": post.author.username} for post in posts]), 200

@app.route('/posts/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    post = Post.query.get_or_404(id)

    if Like.query.filter_by(user_id=current_user.id, post_id=post.id).first():
        return jsonify({"message": "Already liked"}), 400

    like = Like(user_id=current_user.id, post_id=post.id)
    db.session.add(like)
    db.session.commit()
    return jsonify({"message": "Post liked successfully"}), 201

@app.route('/posts/<int:id>/comment', methods=['POST'])
@login_required
def comment_post(id):
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({"message": "Content is required"}), 400

    comment = Comment(content=content, user_id=current_user.id, post_id=id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({"message": "Comment added successfully"}), 201

# Initialize DB
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=5179, debug=True)
