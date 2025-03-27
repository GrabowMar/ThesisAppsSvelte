from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# App Configuration
app = Flask(__name__)
CORS(app)

# In-memory mock data (working as a mock DB for simplicity)
threads = [
    {"id": 1, "title": "Welcome to the Forum", "content": "Introduce yourself!", "category": "General", "comments": []},
    {"id": 2, "title": "Feature Requests", "content": "Post your ideas for features here!", "category": "Feedback", "comments": []}
]
categories = ["General", "Feedback", "Support", "Off-Topic"]

# Routes

@app.route('/api/threads', methods=['GET'])
def get_threads():
    """
    Get all threads with optional query parameters for sorting or filtering by category or search.
    Query params:
        - category (str): Filter threads by category
        - search (str): Search threads by title (case insensitive)
        - sort (str): Sort threads by 'title' or 'id' (default is 'id')
    """
    category = request.args.get('category')
    search = request.args.get('search')
    sort_field = request.args.get('sort', 'id')

    filtered_threads = threads

    if category:
        filtered_threads = [t for t in threads if t['category'].lower() == category.lower()]

    if search:
        filtered_threads = [t for t in filtered_threads if search.lower() in t['title'].lower()]

    if sort_field == 'title':
        filtered_threads = sorted(filtered_threads, key=lambda x: x['title'].lower())
    else:  # Default sort by id
        filtered_threads = sorted(filtered_threads, key=lambda x: x['id'])

    return jsonify(filtered_threads), 200


@app.route('/api/threads', methods=['POST'])
def create_thread():
    """Create a new thread with a title, content, and category."""
    data = request.get_json()
    if not data or not all(key in data for key in ['title', 'content', 'category']):
        return jsonify({"error": "Title, content, and category are required"}), 400

    # Validate category
    if data['category'] not in categories:
        return jsonify({"error": f"Invalid category. Allowed categories: {categories}"}), 400

    new_thread = {
        "id": len(threads) + 1,
        "title": data['title'],
        "content": data['content'],
        "category": data['category'],
        "comments": []
    }
    threads.append(new_thread)
    return jsonify(new_thread), 201


@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def add_comment(thread_id):
    """Add a comment to a specific thread."""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Comment content is required"}), 400

    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({"error": "Thread not found"}), 404

    new_comment = {"id": len(thread['comments']) + 1, "content": data['content']}
    thread['comments'].append(new_comment)

    return jsonify(new_comment), 201


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all available categories."""
    return jsonify(categories), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5255')))
