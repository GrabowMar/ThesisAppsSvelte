from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize application
app = Flask(__name__)
CORS(app)

# Dummy in-memory database for posts and users
posts = [
    {"id": 1, "author": "Alice", "content": "Hello, world!", "likes": 0, "comments": []},
    {"id": 2, "author": "Bob", "content": "Good morning, everyone!", "likes": 2, "comments": ["Hi!", "Good morning!"]},
]
users = [
    {"id": 1, "username": "Alice", "email": "alice@example.com"},
    {"id": 2, "username": "Bob", "email": "bob@example.com"},
]

# Utility function to generate incremental IDs
def get_next_id(dataset):
    return max(item["id"] for item in dataset) + 1 if dataset else 1

### Routes ###

# Test route to verify server is running
@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Server is running!"})

### CRUD for Posts ###
@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    new_post = {
        "id": get_next_id(posts),
        "author": data.get("author", "Anonymous"),
        "content": data.get("content"),
        "likes": 0,
        "comments": []
    }
    posts.append(new_post)
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.json
    for post in posts:
        if post["id"] == post_id:
            post["content"] = data.get("content", post["content"])
            return jsonify(post), 200
    return jsonify({"error": "Post not found"}), 404

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    global posts
    posts = [post for post in posts if post["id"] != post_id]
    return jsonify({"message": "Post deleted"}), 200

### Post Interactions ###
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    for post in posts:
        if post["id"] == post_id:
            post["likes"] += 1
            return jsonify(post), 200
    return jsonify({"error": "Post not found"}), 404

@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    data = request.json
    comment = data.get("comment", "")
    for post in posts:
        if post["id"] == post_id:
            post["comments"].append(comment)
            return jsonify(post), 200
    return jsonify({"error": "Post not found"}), 404

### User Routes ###
@app.route('/api/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    for user in users:
        if user["id"] == user_id:
            return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5259')))
