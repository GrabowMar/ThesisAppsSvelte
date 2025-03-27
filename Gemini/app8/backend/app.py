# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database (In-Memory for simplicity - replace with a real DB for production)
threads = []
comments = {}  # thread_id: [list of comments]
categories = ["General", "Technology", "News", "Off-Topic"]
next_thread_id = 1
next_comment_id = 1


# 4. Authentication Logic (Placeholder - Add real authentication later)
def fake_authenticate(username, password):
    """Placeholder for authentication.  Always returns True."""
    return True


# 5. Utility Functions
def validate_thread_data(data):
    if not all(key in data for key in ("title", "content", "category", "author")):
        return False, "Missing required fields"
    if not data["title"] or not data["content"] or not data["author"]:
        return False, "Fields cannot be empty"
    if data["category"] not in categories:
        return False, "Invalid category"
    return True, None


def validate_comment_data(data):
    if not all(key in data for key in ("content", "author")):
        return False, "Missing required fields"
    if not data["content"] or not data["author"]:
        return False, "Fields cannot be empty"
    return True, None


# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'message': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']

    if fake_authenticate(username, password):  # Replace with real authentication
        return jsonify({'message': 'Login successful', 'username': username})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/api/threads', methods=['GET'])
def get_threads():
    """Returns all threads, optionally sorted by a field."""
    sort_by = request.args.get('sort_by', 'date')  # Default to sorting by date
    order = request.args.get('order', 'desc')  # Default to descending order

    sorted_threads = threads[:]  # Create a copy to avoid modifying the original

    if sort_by == 'date':
        sorted_threads.sort(key=lambda x: x['created_at'], reverse=(order == 'desc'))
    elif sort_by == 'title':
        sorted_threads.sort(key=lambda x: x['title'], reverse=(order == 'desc'))
    # Add other sorting options as needed
    return jsonify(sorted_threads)

@app.route('/api/threads/search', methods=['GET'])
def search_threads():
    """Searches threads based on a query."""
    query = request.args.get('query', '')
    results = [thread for thread in threads if query.lower() in thread['title'].lower() or query.lower() in thread['content'].lower()]
    return jsonify(results)

@app.route('/api/threads', methods=['POST'])
def create_thread():
    """Creates a new thread."""
    global next_thread_id
    data = request.get_json()
    is_valid, message = validate_thread_data(data)
    if not is_valid:
        return jsonify({"message": message}), 400

    new_thread = {
        'id': next_thread_id,
        'title': data['title'],
        'content': data['content'],
        'category': data['category'],
        'author': data['author'],
        'created_at': datetime.datetime.now().isoformat(),
        'comments': []  # Initialize comments list
    }
    threads.append(new_thread)
    next_thread_id += 1
    return jsonify(new_thread), 201


@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Returns a specific thread."""
    thread = next((t for t in threads if t['id'] == thread_id), None)
    if thread is None:
        return jsonify({'message': 'Thread not found'}), 404
    return jsonify(thread)

@app.route('/api/threads/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    """Deletes a specific thread."""
    global threads
    original_length = len(threads)
    threads = [thread for thread in threads if thread['id'] != thread_id]
    if len(threads) == original_length:
        return jsonify({'message': 'Thread not found'}), 404
    del comments[thread_id] #remove comments
    return jsonify({'message': 'Thread deleted'}), 200


@app.route('/api/threads/<int:thread_id>/comments', methods=['GET'])
def get_comments(thread_id):
    """Returns all comments for a specific thread."""
    if thread_id not in comments:
        comments[thread_id] = []
    return jsonify(comments[thread_id])

@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def create_comment(thread_id):
    """Creates a new comment for a specific thread."""
    global next_comment_id
    data = request.get_json()
    is_valid, message = validate_comment_data(data)
    if not is_valid:
        return jsonify({"message": message}), 400

    thread = next((t for t in threads if t['id'] == thread_id), None)
    if not thread:
        return jsonify({'message': 'Thread not found'}), 404

    new_comment = {
        'id': next_comment_id,
        'thread_id': thread_id,
        'content': data['content'],
        'author': data['author'],
        'created_at': datetime.datetime.now().isoformat()
    }

    if thread_id not in comments:
        comments[thread_id] = []
    comments[thread_id].append(new_comment)

    next_comment_id += 1
    return jsonify(new_comment), 201


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Returns the list of categories."""
    return jsonify(categories)


# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5415')), debug=True)
