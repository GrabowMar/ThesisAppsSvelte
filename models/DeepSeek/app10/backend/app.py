# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# In-memory data storage for simplicity
posts = []
users = []

# 3. Utility Functions
def find_post(post_id):
    return next((post for post in posts if post['id'] == post_id), None)

def find_user(user_id):
    return next((user for user in users if user['id'] == user_id), None)

# 4. API Routes
@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts)

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404)
    return jsonify(post)

@app.route('/api/posts', methods=['POST'])
def create_post():
    new_post = request.json
    new_post['id'] = len(posts) + 1
    posts.append(new_post)
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404)
    post.update(request.json)
    return jsonify(post)

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global posts
    post = find_post(post_id)
    if post is None:
        abort(404)
    posts = [p for p in posts if p['id'] != post_id]
    return jsonify({'message': 'Post deleted'})

@app.route('/api/users', methods=['POST'])
def create_user():
    new_user = request.json
    new_user['id'] = len(users) + 1
    users.append(new_user)
    return jsonify(new_user), 201

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = find_user(user_id)
    if user is None:
        abort(404)
    return jsonify(user)

# 5. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5679')))
