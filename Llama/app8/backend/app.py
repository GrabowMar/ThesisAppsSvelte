# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory data store for simplicity (in a real application, use a database)
threads = [
    {"id": 1, "title": "Thread 1", "category": "Category 1", "comments": []},
    {"id": 2, "title": "Thread 2", "category": "Category 2", "comments": []},
]

# Thread creation
@app.route('/threads', methods=['POST'])
def create_thread():
    """Create a new thread."""
    data = request.json
    if 'title' not in data or 'category' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    new_thread = {
        "id": len(threads) + 1,
        "title": data['title'],
        "category": data['category'],
        "comments": []
    }
    threads.append(new_thread)
    return jsonify(new_thread), 201

# Thread viewing
@app.route('/threads', methods=['GET'])
def get_threads():
    """Get all threads."""
    return jsonify(threads)

# Thread viewing by ID
@app.route('/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Get a thread by ID."""
    thread = next((thread for thread in threads if thread['id'] == thread_id), None)
    if thread is None:
        return jsonify({"error": "Thread not found"}), 404
    return jsonify(thread)

# Comment creation
@app.route('/threads/<int:thread_id>/comments', methods=['POST'])
def create_comment(thread_id):
    """Create a new comment for a thread."""
    thread = next((thread for thread in threads if thread['id'] == thread_id), None)
    if thread is None:
        return jsonify({"error": "Thread not found"}), 404
    
    data = request.json
    if 'content' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    new_comment = {
        "id": len(thread['comments']) + 1,
        "content": data['content']
    }
    thread['comments'].append(new_comment)
    return jsonify(new_comment), 201

# Comment viewing
@app.route('/threads/<int:thread_id>/comments', methods=['GET'])
def get_comments(thread_id):
    """Get all comments for a thread."""
    thread = next((thread for thread in threads if thread['id'] == thread_id), None)
    if thread is None:
        return jsonify({"error": "Thread not found"}), 404
    return jsonify(thread['comments'])

# Thread search
@app.route('/threads/search', methods=['GET'])
def search_threads():
    """Search threads by title."""
    query = request.args.get('query', '')
    results = [thread for thread in threads if query.lower() in thread['title'].lower()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5015)
