from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from functools import wraps
import os
import jwt
import datetime
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(24)

# In-memory database simulation (replace with actual database in production)
users = {}
posts = {}
categories = {
    "technology": "Technology",
    "science": "Science",
    "arts": "Arts",
    "sports": "Sports"
}

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = users.get(data['public_id'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# User Authentication
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = {
        'public_id': str(uuid.uuid4()),
        'username': data['username'],
        'password': hashed_password
    }
    users[user['public_id']] = user
    return jsonify({'message': 'Registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'message': 'Could not verify'}), 401
    user = next((user for user in users.values() if user['username'] == auth.username), None)
    if not user:
        return jsonify({'message': 'User not found'}), 401
    if bcrypt.check_password_hash(user['password'], auth.password):
        token = jwt.encode({'public_id': user['public_id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.secret_key)
        return jsonify({'token': token})
    return jsonify({'message': 'Could not verify'}), 401

# Blog Post Management
@app.route('/post', methods=['POST'])
@token_required
def create_post(current_user):
    data = request.get_json()
    post_id = str(uuid.uuid4())
    posts[post_id] = {
        'id': post_id,
        'author': current_user['username'],
        'title': data['title'],
        'content': data['content'],
        'category': data['category'],
        'comments': []
    }
    return jsonify({'message': 'Post created successfully', 'post_id': post_id}), 201

@app.route('/post/<post_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_post(current_user, post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    if current_user['username'] != post['author']:
        return jsonify({'message': 'Unauthorized to edit/delete this post'}), 403

    if request.method == 'GET':
        return jsonify(post), 200
    elif request.method == 'PUT':
        data = request.get_json()
        post['title'] = data.get('title', post['title'])
        post['content'] = data.get('content', post['content'])
        post['category'] = data.get('category', post['category'])
        return jsonify({'message': 'Post updated successfully'}), 200
    elif request.method == 'DELETE':
        del posts[post_id]
        return jsonify({'message': 'Post deleted successfully'}), 200

# Comment Management
@app.route('/post/<post_id>/comment', methods=['POST'])
@token_required
def create_comment(current_user, post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    data = request.get_json()
    comment_id = str(uuid.uuid4())
    comment = {
        'id': comment_id,
        'author': current_user['username'],
        'content': data['content']
    }
    post['comments'].append(comment)
    return jsonify({'message': 'Comment added successfully', 'comment_id': comment_id}), 201

# Category Management
@app.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(list(categories.values())), 200

# Error Handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5987')))
