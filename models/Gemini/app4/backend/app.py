from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
import os
import bcrypt
import secrets
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True) # Needed for cookies
app.secret_key = secrets.token_hex(16)  # Strong secret key for sessions

# Dummy Data (Replace with a Database in a real application)
users = {}  # Username: {password_hash: ..., posts: [...]}
posts = [] # {id: ..., title: ..., content: ..., author: ..., category: ..., comments: [...]}
next_post_id = 1

# Utility functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)


# API Routes

# User Authentication
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'message': 'Username already exists'}), 409

    hashed_password = hash_password(password)
    users[username] = {'password_hash': hashed_password, 'posts': []}

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if username not in users:
        return jsonify({'message': 'Invalid credentials'}), 401

    user = users[username]
    if verify_password(password, user['password_hash']):
        session['username'] = username  # Store username in session
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove username from session
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/is_logged_in', methods=['GET'])
def is_logged_in():
    if 'username' in session:
        return jsonify({'isLoggedIn': True, 'username': session['username']}), 200
    else:
        return jsonify({'isLoggedIn': False}), 200

# Blog Post Management
@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts), 200

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    for post in posts:
        if post['id'] == post_id:
            return jsonify(post), 200
    return jsonify({'message': 'Post not found'}), 404

@app.route('/api/posts', methods=['POST'])
def create_post():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category', 'Uncategorized')  # Default category

    if not title or not content:
        return jsonify({'message': 'Title and content are required'}), 400

    global next_post_id
    new_post = {
        'id': next_post_id,
        'title': title,
        'content': content,
        'author': session['username'],
        'category': category,
        'comments': [],
        'date': datetime.now().isoformat()
    }
    posts.append(new_post)
    users[session['username']]['posts'].append(new_post['id']) #Store which post belongs to which user
    next_post_id += 1
    return jsonify({'message': 'Post created successfully', 'post': new_post}), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    category = data.get('category')

    for post in posts:
        if post['id'] == post_id and post['author'] == session['username']:
            if title:
                post['title'] = title
            if content:
                post['content'] = content
            if category:
                post['category'] = category
            return jsonify({'message': 'Post updated successfully', 'post': post}), 200

    return jsonify({'message': 'Post not found or unauthorized'}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    for i, post in enumerate(posts):
        if post['id'] == post_id and post['author'] == session['username']:
            del posts[i]
            #Also remove the post ID from the user's post list
            users[session['username']]['posts'] = [p for p in users[session['username']]['posts'] if p != post_id]
            return jsonify({'message': 'Post deleted successfully'}), 200

    return jsonify({'message': 'Post not found or unauthorized'}), 404

# Comment System
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({'message': 'Comment text is required'}), 400

    for post in posts:
        if post['id'] == post_id:
            comment = {'author': session['username'], 'text': text}
            post['comments'].append(comment)
            return jsonify({'message': 'Comment added successfully', 'comment': comment}), 201

    return jsonify({'message': 'Post not found'}), 404

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5407')), debug=True)
