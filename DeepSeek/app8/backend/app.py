from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory database (for simplicity)
threads = []
next_thread_id = 1
next_comment_id = 1

# Utility Functions
def find_thread(thread_id):
    return next((t for t in threads if t['id'] == thread_id), None)

# API Routes
@app.route('/api/threads', methods=['GET'])
def get_threads():
    category = request.args.get('category')
    search = request.args.get('search')
    sort = request.args.get('sort', 'latest')

    filtered_threads = threads

    if category:
        filtered_threads = [t for t in filtered_threads if t['category'] == category]
    if search:
        filtered_threads = [t for t in filtered_threads if search.lower() in t['title'].lower()]

    if sort == 'latest':
        filtered_threads.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort == 'oldest':
        filtered_threads.sort(key=lambda x: x['created_at'])

    return jsonify(filtered_threads)

@app.route('/api/threads', methods=['POST'])
def create_thread():
    global next_thread_id
    data = request.json
    if not data or not data.get('title') or not data.get('category'):
        abort(400, description="Title and category are required.")

    new_thread = {
        'id': next_thread_id,
        'title': data['title'],
        'category': data['category'],
        'content': data.get('content', ''),
        'created_at': '2023-10-01',  # Replace with actual timestamp
        'comments': []
    }
    threads.append(new_thread)
    next_thread_id += 1
    return jsonify(new_thread), 201

@app.route('/api/threads/<int:thread_id>/comments', methods=['POST'])
def add_comment(thread_id):
    global next_comment_id
    data = request.json
    if not data or not data.get('content'):
        abort(400, description="Comment content is required.")

    thread = find_thread(thread_id)
    if not thread:
        abort(404, description="Thread not found.")

    new_comment = {
        'id': next_comment_id,
        'content': data['content'],
        'created_at': '2023-10-01'  # Replace with actual timestamp
    }
    thread['comments'].append(new_comment)
    next_comment_id += 1
    return jsonify(new_comment), 201

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5175)
