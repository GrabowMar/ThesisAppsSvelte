# 1. Imports
from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import markdown
import os

# 2. App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, resources={r"/api/*": {"origins": "http://localhost:6067"}})

# 3. Database Setup
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# 4. Authentication Helpers
def create_token(user_id):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
        'iat': datetime.datetime.utcnow(),
        'sub': user_id
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
            
        if not token:
            abort(401, "Authentication required")
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['sub'])
        except:
            abort(401, "Invalid token")
        
        return f(current_user, *args, **kwargs)
    return decorator

# 5. Utility Functions
def markdown_to_html(content):
    return markdown.markdown(content)

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        abort(400, "Username already exists")
    
    hashed_pw = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        abort(401, "Invalid credentials")
    
    token = create_token(user.id)
    return jsonify({"token": token, "user_id": user.id})

@app.route('/api/posts', methods=['GET'])
def get_posts():
    category = request.args.get('category')
    query = Post.query.order_by(Post.created_at.desc())
    
    if category:
        query = query.filter_by(category=category)
        
    posts = query.all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'content': markdown_to_html(p.content),
        'category': p.category,
        'author': User.query.get(p.user_id).username,
        'created_at': p.created_at.isoformat()
    } for p in posts])

@app.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.get_json()
    new_post = Post(
        title=data['title'],
        content=data['content'],
        category=data['category'],
        user_id=current_user.id
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"message": "Post created"}), 201

# 7. Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": error.description}), 401

# Initialize Database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5567')))
