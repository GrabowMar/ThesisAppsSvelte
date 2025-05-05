"""
app.py – Backend for the Blog Application built with Flask.
Ports: 6147 (backend)
Features:
 - User authentication (register, login) with in-memory storage.
 - CRUD endpoints for blog posts.
 - Comment system per post.
 - Markdown processing support via the markdown library.
 - Error handling and CORS enabled.
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import markdown
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory storage (for production, use a proper DB)
users = {}       # {'username': {'password': '...', 'posts': []}}
posts = {}       # {post_id: { 'title': '...', 'content': '...', 'author': 'username', 'created': datetime, 'comments': [ { 'author':..., 'content': ... } ] }}
post_counter = 1

# Helper: Authentication check (dummy, production should use hashed passwords and tokens)
def authenticate(username, password):
    user = users.get(username)
    if user and user['password'] == password:
        return True
    return False

# Route: User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if username in users:
        return jsonify({"error": "User already exists"}), 400
    
    users[username] = {"password": password, "posts": []}
    return jsonify({"message": "Registration successful"}), 201

# Route: User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if authenticate(username, password):
        return jsonify({"message": "Login successful", "username": username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# Route: Get All Posts
@app.route('/api/posts', methods=['GET'])
def get_posts():
    result = []
    for post_id, post in posts.items():
        result.append({
            "id": post_id,
            "title": post["title"],
            "author": post["author"],
            "created": post["created"].isoformat()
        })
    return jsonify(result), 200

# Route: Create a New Post
@app.route('/api/posts', methods=['POST'])
def create_post():
    global post_counter
    data = request.get_json()
    username = data.get("author")
    title = data.get("title")
    content = data.get("content")

    if not username or not title or not content:
        return jsonify({"error": "Author, title, and content are required."}), 400
    
    # In a production app, user authentication should be validated
    if username not in users:
        return jsonify({"error": "Invalid author."}), 400
    
    posts[post_counter] = {
        "title": title,
        "content": content,
        "author": username,
        "created": datetime.utcnow(),
        "comments": []
    }
    # Add post id to user's posts
    users[username]["posts"].append(post_counter)
    post_counter += 1
    return jsonify({"message": "Post created successfully"}), 201

# Route: Get a Post (with Markdown rendered HTML)
@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    # Render markdown content to HTML (for preview)
    html_content = markdown.markdown(post["content"])
    response = {
        "id": post_id,
        "title": post["title"],
        "content": html_content,
        "author": post["author"],
        "created": post["created"].isoformat(),
        "comments": post["comments"],
    }
    return jsonify(response), 200

# Route: Edit Post
@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def edit_post(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    data = request.get_json()
    update_title = data.get("title")
    update_content = data.get("content")
    username = data.get("author")

    # Check that only the original author can update the post
    if post["author"] != username:
        return jsonify({"error": "Permission denied."}), 403

    if update_title:
        post["title"] = update_title
    if update_content:
        post["content"] = update_content
    return jsonify({"message": "Post updated successfully"}), 200

# Route: Delete Post
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.get_json() or {}
    username = data.get("author")
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post["author"] != username:
        return jsonify({"error": "Permission denied."}), 403
    # Remove post id from user's list
    if username in users:
        if post_id in users[username]["posts"]:
            users[username]["posts"].remove(post_id)
    del posts[post_id]
    return jsonify({"message": "Post deleted successfully"}), 200

# Route: Add a Comment to a Post
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    post = posts.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    data = request.get_json()
    comment_author = data.get("author")
    comment_content = data.get("content")
    if not comment_author or not comment_content:
        return jsonify({"error": "Comment author and content required."}), 400
    # In production, validate comment_author properly.
    comment = {
        "author": comment_author,
        "content": comment_content,
        "created": datetime.utcnow().isoformat()
    }
    post["comments"].append(comment)
    return jsonify({"message": "Comment added successfully"}), 201

# Global error handler for unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal server error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run backend on port 6147
    port = int(os.getenv('PORT', '6147'))
    app.run(host='0.0.0.0', port=port)
