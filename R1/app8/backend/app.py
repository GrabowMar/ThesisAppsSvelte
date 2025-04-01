from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os
import uuid

app = Flask(__name__)
CORS(app)

# In-memory data storage
threads = []
categories = ['General', 'Technology', 'Gaming', 'Art', 'Science']

# Helper functions
def find_thread(thread_id):
    return next((t for t in threads if t['id'] == thread_id), None)

# API Routes
@app.route('/api/threads', methods=['GET'])
def get_threads():
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'date')
    category = request.args.get('category', '')
    
    filtered = [t for t in threads if 
               (search.lower() in t['title'].lower() or search.lower() in t['content'].lower()) and
               (category == '' or t['category'] == category)]
    
    if sort == 'comments':
        filtered.sort(key=lambda x: len(x['comments']), reverse=True)
    else:
        filtered.sort(key=lambda x: x['date'], reverse=True)
        
    return jsonify(filtered)

@app.route('/api/threads', methods=['POST'])
def create_thread():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        abort(400)
    
    new_thread = {
        'id': str(uuid.uuid4()),
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', 'General'),
        'author': data.get('author', 'Anonymous'),
        'date': datetime.now().isoformat(),
        'comments': []
    }
    threads.append(new_thread)
    return jsonify(new_thread), 201

@app.route('/api/threads/<string:thread_id>/comments', methods=['POST'])
def add_comment(thread_id):
    thread = find_thread(thread_id)
    if not thread:
        abort(404)
    
    data = request.get_json()
    if not data or 'content' not in data:
        abort(400)
    
    new_comment = {
        'id': str(uuid.uuid4()),
        'content': data['content'],
        'author': data.get('author', 'Anonymous'),
        'date': datetime.now().isoformat()
    }
    
    thread['comments'].append(new_comment)
    return jsonify(new_comment), 201

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5575')))
