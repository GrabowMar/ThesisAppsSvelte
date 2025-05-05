from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

# SAMPLE Database simulation
users = {}
posts = []

# Initialize App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret')
CORS(app)

# ------- Utility Functions ------- #

def get_authenticated_user():
    """Utility to fetch currently authenticated user"""
    user_email = session.get('email')
    if user_email and users.get(user_email):
        return users[user_email]
    return None

# ------- Routes ------- #

# Home route
@app.route('/')
def welcome():
    return jsonify({'message': 'Welcome to the Blog System!'})

# User Authentication
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    if email in users:
        return jsonify({'error': 'User already exists'}), 400

    hashed_password = generate_password_hash(password)
    users[email] = {'email': email, 'password': hashed_password}
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = users.get(email)
    if not user or not check_password_hash(user['password'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    session['email'] = email
    return jsonify({'message': 'Login successful', 'email': email}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('email', None)
    return jsonify({'message': 'Logged out'}), 200

# Blog API
@app.route('/api/posts', methods=['GET', 'POST'])
def manage_posts():
    user = get_authenticated_user()
    if not user:
        return jsonify({'error': 'Unauthorized access'}), 403

    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        content = data.get('content')

        if not title or not content:
            return jsonify({'error': 'Title and content are required'}), 400

        post = {
            'id': len(posts) + 1,
            'title': title,
            'content': content,
            'author': user['email']
        }
        posts.append(post)
        return jsonify({'message': 'Post created', 'post': post}), 201

    # GET
    return jsonify({'posts': posts}), 200

@app.route('/api/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_single_post(post_id):
    user = get_authenticated_user()
    if not user:
        return jsonify({'error': 'Unauthorized access'}), 403

    post = next((post for post in posts if post['id'] == post_id), None)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    if request.method == 'PUT':
        data = request.json
        post['title'] = data.get('title', post['title'])
        post['content'] = data.get('content', post['content'])
        return jsonify({'message': 'Post updated', 'post': post}), 200

    if request.method == 'DELETE':
        posts.remove(post)
        return jsonify({'message': 'Post deleted'}), 200

    return jsonify({'post': post}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5747)
