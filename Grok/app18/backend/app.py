from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
from datetime import datetime
import json

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory storage for demonstration purposes
# In a production environment, use a proper database
wiki_pages = {}

@app.route('/api/pages', methods=['GET'])
def get_all_pages():
    """Retrieve all wiki pages"""
    return jsonify(list(wiki_pages.keys()))

@app.route('/api/pages/<string:page_id>', methods=['GET'])
def get_page(page_id):
    """Retrieve a specific wiki page"""
    if page_id not in wiki_pages:
        abort(404)
    return jsonify(wiki_pages[page_id])

@app.route('/api/pages', methods=['POST'])
def create_page():
    """Create a new wiki page"""
    data = request.json
    if not data or 'title' not in data:
        abort(400)
    page_id = data['title'].lower().replace(' ', '_')
    if page_id in wiki_pages:
        abort(409)
    wiki_pages[page_id] = {
        'title': data['title'],
        'content': data.get('content', ''),
        'history': [{
            'timestamp': datetime.utcnow().isoformat(),
            'content': data.get('content', '')
        }]
    }
    return jsonify({'page_id': page_id}), 201

@app.route('/api/pages/<string:page_id>', methods=['PUT'])
def update_page(page_id):
    """Update an existing wiki page"""
    if page_id not in wiki_pages:
        abort(404)
    data = request.json
    if not data or 'content' not in data:
        abort(400)
    wiki_pages[page_id]['content'] = data['content']
    wiki_pages[page_id]['history'].append({
        'timestamp': datetime.utcnow().isoformat(),
        'content': data['content']
    })
    return jsonify(wiki_pages[page_id])

@app.route('/api/pages/<string:page_id>/history', methods=['GET'])
def get_page_history(page_id):
    """Retrieve the version history of a wiki page"""
    if page_id not in wiki_pages:
        abort(404)
    return jsonify(wiki_pages[page_id]['history'])

@app.route('/api/search', methods=['GET'])
def search_pages():
    """Search wiki pages by keyword"""
    query = request.args.get('q', '')
    results = [
        page_id for page_id in wiki_pages
        if query.lower() in wiki_pages[page_id]['title'].lower() or
           query.lower() in wiki_pages[page_id]['content'].lower()
    ]
    return jsonify(results)

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(409)
def conflict(error):
    return jsonify({'error': 'Conflict'}), 409

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6015')))
