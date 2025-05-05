# app/backend/app.py

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import datetime

app = Flask(__name__)
CORS(app)

# In-memory "databases"
users = {}
threads = {}
comments = {}
thread_counter = 1
comment_counter = 1

# Utility: timestamp generator
def current_timestamp():
    return datetime.datetime.utcnow().isoformat() + "Z"

# ---------------------------
# Authentication Endpoints
# ---------------------------

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": "Missing username or password."}), 400

        if username in users:
            return jsonify({"error": "User already exists."}), 400

        # In production, never store plain passwords.
        users[username] = {"username": username, "password": password}
        return jsonify({"message": "Registration successful."}), 201
    except Exception as e:
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"error": "Missing username or password."}), 400

        user = users.get(username)
        if not user or user.get('password') != password:
            return jsonify({"error": "Invalid credentials."}), 401

        # In a production app return a session token or JWT
        return jsonify({"message": "Login successful.", "user": username}), 200
    except Exception as e:
        return jsonify({"error": f"Login failed: {str(e)}"}), 500

# ---------------------------
# Thread Endpoints
# ---------------------------

@app.route('/api/threads', methods=['GET'])
def get_threads():
    """Get list of threads. Accepts optional query parameters:
       - search: keyword contained in title or content
       - category: filter by category
       - sort: "asc" or "desc" (by creation timestamp)
    """
    try:
        search_term = request.args.get('search', '').lower()
        category_filter = request.args.get('category', '').lower()
        sort_order = request.args.get('sort', 'desc')

        thread_list = list(threads.values())

        # Filter by search term
        if search_term:
            thread_list = [t for t in thread_list if search_term in t['title'].lower() or search_term in t['content'].lower()]

        # Filter by category
        if category_filter:
            thread_list = [t for t in thread_list if t.get('category', '').lower() == category_filter]

        # Sort threads by timestamp
        thread_list = sorted(thread_list, key=lambda x: x['created_at'], reverse=(sort_order == 'desc'))

        return jsonify(thread_list), 200
    except Exception as e:
        return jsonify({"error": f"Could not fetch threads: {str(e)}"}), 500

@app.route('/api/threads', methods=['POST'])
def create_thread():
    global thread_counter
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        category = data.get('category', 'General')
        author = data.get('author')
        if not title or not content or not author:
            return jsonify({"error": "Title, content and author are required."}), 400

        thread = {
            "id": thread_counter,
            "title": title,
            "content": content,
            "category": category,
            "author": author,
            "created_at": current_timestamp(),
            "comments": []  # List of comment ids
        }
        threads[thread_counter] = thread
        thread_counter += 1

        return jsonify(thread), 201
    except Exception as e:
        return jsonify({"error": f"Could not create thread: {str(e)}"}), 500

@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    try:
        thread = threads.get(thread_id)
        if not thread:
            abort(404, description="Thread not found.")
        # Also include comments for the thread:
        thread_comments = [comments[cid] for cid in thread.get("comments", [])]
        thread_detail = dict(thread)
        thread_detail["comments"] = thread_comments
        return jsonify(thread_detail), 200
    except Exception as e:
        return jsonify({"error": f"Could not fetch thread: {str(e)}"}), 500

# ---------------------------
# Comment Endpoints
# ---------------------------

@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def add_comment(thread_id):
    global comment_counter
    try:
        if thread_id not in threads:
            abort(404, description="Thread not found.")
        data = request.get_json()
        content = data.get('content')
        author = data.get('author')
        if not content or not author:
            return jsonify({"error": "Comment content and author required."}), 400

        comment = {
            "id": comment_counter,
            "thread_id": thread_id,
            "content": content,
            "author": author,
            "created_at": current_timestamp()
        }
        comments[comment_counter] = comment
        threads[thread_id]["comments"].append(comment_counter)
        comment_counter += 1

        return jsonify(comment), 201
    except Exception as e:
        return jsonify({"error": f"Could not add comment: {str(e)}"}), 500

# ---------------------------
# Example Dashboard Endpoint
# ---------------------------
@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    # In a real-world app, protect this route with authentication.
    return jsonify({
        "message": "Welcome to your dashboard.",
        "threads_count": len(threads),
        "users_count": len(users)
    }), 200

# ---------------------------
# Error Handlers
# ---------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description if hasattr(error, "description") else "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error."}), 500

# ---------------------------
# App Runner
# ---------------------------
if __name__ == '__main__':
    port = int(os.getenv('PORT', '5655'))
    app.run(host='0.0.0.0', port=port)
