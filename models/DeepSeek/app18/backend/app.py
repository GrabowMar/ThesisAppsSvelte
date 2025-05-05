from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# In-memory storage for pages and version history
pages = {}
version_history = {}

# Utility functions
def create_page(title, content):
    page_id = str(len(pages) + 1)
    pages[page_id] = {"title": title, "content": content}
    version_history[page_id] = [{"content": content, "timestamp": datetime.now().isoformat()}]
    return page_id

def update_page(page_id, content):
    if page_id not in pages:
        abort(404, description="Page not found")
    pages[page_id]["content"] = content
    version_history[page_id].append({"content": content, "timestamp": datetime.now().isoformat()})

def get_page(page_id):
    if page_id not in pages:
        abort(404, description="Page not found")
    return pages[page_id]

def search_pages(query):
    results = []
    for page_id, page in pages.items():
        if query.lower() in page["title"].lower() or query.lower() in page["content"].lower():
            results.append({"id": page_id, **page})
    return results

# API Routes
@app.route('/api/pages', methods=['GET'])
def list_pages():
    return jsonify([{"id": page_id, **page} for page_id, page in pages.items()])

@app.route('/api/pages', methods=['POST'])
def add_page():
    data = request.json
    page_id = create_page(data["title"], data["content"])
    return jsonify({"id": page_id, **pages[page_id]})

@app.route('/api/pages/<page_id>', methods=['GET'])
def fetch_page(page_id):
    return jsonify(get_page(page_id))

@app.route('/api/pages/<page_id>', methods=['PUT'])
def edit_page(page_id):
    data = request.json
    update_page(page_id, data["content"])
    return jsonify(get_page(page_id))

@app.route('/api/pages/<page_id>/history', methods=['GET'])
def fetch_history(page_id):
    if page_id not in version_history:
        abort(404, description="Page not found")
    return jsonify(version_history[page_id])

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    return jsonify(search_pages(query))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5195')))
