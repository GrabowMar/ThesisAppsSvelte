# app/backend/app.py

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# In-memory data storage
threads = []
categories = ["General", "Tech", "Science", "Sports"]

# Helper function to find a thread by ID
def find_thread(thread_id):
    return next((t for t in threads if t["id"] == thread_id), None)

# Routes
@app.route("/")
def index():
    return "Forum Backend is running!"

# Get all threads
@app.route("/threads", methods=["GET"])
def get_threads():
    category = request.args.get("category")
    sort_by = request.args.get("sort_by", "latest")  # "latest" or "popular"
    search_query = request.args.get("search", "")

    filtered_threads = threads

    # Filter by category
    if category:
        filtered_threads = [t for t in filtered_threads if t["category"] == category]

    # Filter by search query
    if search_query:
        filtered_threads = [
            t for t in filtered_threads
            if search_query.lower() in t["title"].lower() or search_query.lower() in t["content"].lower()
        ]

    # Sort threads
    if sort_by == "latest":
        filtered_threads.sort(key=lambda t: t["timestamp"], reverse=True)
    elif sort_by == "popular":
        filtered_threads.sort(key=lambda t: len(t["comments"]), reverse=True)

    return jsonify(filtered_threads)

# Create a new thread
@app.route("/threads", methods=["POST"])
def create_thread():
    data = request.json
    if not data or not data.get("title") or not data.get("content") or not data.get("category"):
        abort(400, description="Missing required fields: title, content, or category")

    new_thread = {
        "id": str(uuid.uuid4()),
        "title": data["title"],
        "content": data["content"],
        "category": data["category"],
        "timestamp": "2023-10-01T00:00:00Z",  # Replace with actual timestamp logic
        "comments": [],
    }
    threads.append(new_thread)
    return jsonify(new_thread), 201

# Add a comment to a thread
@app.route("/threads/<thread_id>/comments", methods=["POST"])
def add_comment(thread_id):
    thread = find_thread(thread_id)
    if not thread:
        abort(404, description="Thread not found")

    data = request.json
    if not data or not data.get("content"):
        abort(400, description="Missing required field: content")

    new_comment = {
        "id": str(uuid.uuid4()),
        "content": data["content"],
        "timestamp": "2023-10-01T00:00:00Z",  # Replace with actual timestamp logic
    }
    thread["comments"].append(new_comment)
    return jsonify(new_comment), 201

# Get all categories
@app.route("/categories", methods=["GET"])
def get_categories():
    return jsonify(categories)

# Error handler
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5175)
