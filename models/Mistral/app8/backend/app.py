from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database Models (example)
threads = []
comments = []
categories = []

# Utility Functions
def find_thread(thread_id):
    return next((thread for thread in threads if thread['id'] == thread_id), None)

# API Routes
@app.route('/api/threads', methods=['GET', 'POST'])
def handle_threads():
    if request.method == 'POST':
        data = request.get_json()
        thread_id = len(threads) + 1
        new_thread = {
            'id': thread_id,
            'title': data['title'],
            'content': data['content'],
            'category': data['category'],
            'comments': []
        }
        threads.append(new_thread)
        return jsonify(new_thread), 201
    else:
        return jsonify(threads)

@app.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    thread = find_thread(thread_id)
    if thread:
        return jsonify(thread)
    else:
        return jsonify({'error': 'Thread not found'}), 404

@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def add_comment(thread_id):
    thread = find_thread(thread_id)
    if thread:
        data = request.get_json()
        comment_id = len(comments) + 1
        new_comment = {
            'id': comment_id,
            'content': data['content'],
            'thread_id': thread_id
        }
        comments.append(new_comment)
        thread['comments'].append(new_comment)
        return jsonify(new_comment), 201
    else:
        return jsonify({'error': 'Thread not found'}), 404

@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(categories)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5095')))
