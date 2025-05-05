# 1. Imports
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False

# 3. Data Storage
pages = [
    {
        'id': 1,
        'title': 'Welcome',
        'content': '# Welcome to our Wiki!\nStart editing or create new pages.',
        'created_at': datetime.now().isoformat(),
        'versions': [
            {'content': '# Welcome to our Wiki!\nStart editing or create new pages.', 
             'timestamp': datetime.now().isoformat()}
        ]
    }
]
next_id = 2

# 4. Utility Functions
def find_page(page_id):
    return next((p for p in pages if p['id'] == page_id), None)

# 5. API Routes
@app.route('/api/pages', methods=['GET'])
def list_pages():
    query = request.args.get('query', '').lower()
    filtered = [p for p in pages if 
                query in p['title'].lower() or 
                query in p['content'].lower()]
    return jsonify([{'id': p['id'], 'title': p['title']} for p in filtered])

@app.route('/api/pages', methods=['POST'])
def create_page():
    global next_id
    data = request.get_json()
    if not data.get('title') or not data.get('content'):
        abort(400, 'Title and content required')
    
    new_page = {
        'id': next_id,
        'title': data['title'],
        'content': data['content'],
        'created_at': datetime.now().isoformat(),
        'versions': [{'content': data['content'], 
                      'timestamp': datetime.now().isoformat()}]
    }
    pages.append(new_page)
    next_id += 1
    return jsonify(new_page), 201

@app.route('/api/pages/<int:page_id>', methods=['GET'])
def get_page(page_id):
    page = find_page(page_id)
    if not page:
        abort(404, 'Page not found')
    return jsonify(page)

@app.route('/api/pages/<int:page_id>', methods=['PUT'])
def update_page(page_id):
    page = find_page(page_id)
    if not page:
        abort(404, 'Page not found')
    
    data = request.get_json()
    if 'title' not in data and 'content' not in data:
        abort(400, 'No changes provided')
    
    # Save current version
    page['versions'].append({
        'content': page['content'],
        'timestamp': datetime.now().isoformat()
    })
    
    if 'title' in data: page['title'] = data['title']
    if 'content' in data: page['content'] = data['content']
    return jsonify(page)

@app.route('/api/pages/<int:page_id>/versions', methods=['GET'])
def get_versions(page_id):
    page = find_page(page_id)
    if not page:
        abort(404, 'Page not found')
    return jsonify(page['versions'])

# 6. Error Handlers
@app.errorhandler(404)
@app.errorhandler(400)
def handle_error(e):
    return jsonify({'error': e.description}), e.code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5595')))
