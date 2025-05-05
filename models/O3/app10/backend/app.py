# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory "Database" for Posts and Users
posts = []
post_id_counter = 1

# Sample structure for a post:
# {
#   "id": 1,
#   "author": "johndoe",
#   "content": "Hello world",
#   "likes": 0,
#   "comments": [
#       { "author": "janedoe", "content": "Nice post!" }
#   ]
# }

# In-memory user data (for demo purposes)
users = {
    "johndoe": {"username": "johndoe", "bio": "Hello, I am John."},
    "janedoe": {"username": "janedoe", "bio": "Jane here!"}
}

# 4. Utility Functions
def find_post(post_id):
    return next((post for post in posts if post["id"] == post_id), None)

# 5. API Routes

# GET all posts (timeline/feed)
@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify({"posts": posts}), 200

# POST create a new post
@app.route('/api/posts', methods=['POST'])
def create_post():
    global post_id_counter
    data = request.get_json()
    if not data or "author" not in data or "content" not in data:
        abort(400, description="Missing 'author' or 'content' in request data.")
    
    new_post = {
        "id": post_id_counter,
        "author": data["author"],
        "content": data["content"],
        "likes": 0,
        "comments": []
    }
    posts.insert(0, new_post)  # insert at beginning for recent-first timeline
    post_id_counter += 1
    return jsonify(new_post), 201

# GET a specific post
@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404, description="Post not found.")
    return jsonify(post), 200

# PUT update a post
@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404, description="Post not found.")
    
    data = request.get_json()
    # Update content if provided; you could extend to update author or other fields.
    if "content" in data:
        post["content"] = data["content"]
    else:
        abort(400, description="Missing 'content' in request data.")
    return jsonify(post), 200

# DELETE remove a post
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404, description="Post not found.")
    posts.remove(post)
    return jsonify({"message": "Post deleted."}), 200

# POST like a post
@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404, description="Post not found.")
    post["likes"] += 1
    return jsonify({"likes": post["likes"]}), 200

# POST add comment to a post
@app.route('/api/posts/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    post = find_post(post_id)
    if post is None:
        abort(404, description="Post not found.")
    
    data = request.get_json()
    if not data or "author" not in data or "content" not in data:
        abort(400, description="Missing 'author' or 'content' in request data.")
    
    comment = {"author": data["author"], "content": data["content"]}
    post["comments"].append(comment)
    return jsonify({"comments": post["comments"]}), 200

# GET user profile
@app.route('/api/users/<string:username>', methods=['GET'])
def get_user_profile(username):
    user = users.get(username)
    if user is None:
        abort(404, description="User not found.")
    return jsonify(user), 200

# PUT update user profile
@app.route('/api/users/<string:username>', methods=['PUT'])
def update_user_profile(username):
    user = users.get(username)
    if user is None:
        abort(404, description="User not found.")
    data = request.get_json()
    if "bio" in data:
        user["bio"] = data["bio"]
    return jsonify(user), 200

# Basic error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server error, please try again later."}), 500

# 6. Application Runner
if __name__ == '__main__':
    # Use port 6159 for backend per requirements.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6159')), debug=False)
