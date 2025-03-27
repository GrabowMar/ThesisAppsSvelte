# app/backend/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import datetime

app = Flask(__name__)
CORS(app)

# In-memory data store (replace with a database in a real application)
wiki_pages = {
    "home": {
        "title": "Home",
        "content": "Welcome to the Wiki!",
        "history": [{"timestamp": datetime.datetime.now().isoformat(), "content": "Welcome to the Wiki!"}]
    },
    "about": {
        "title": "About",
        "content": "This is a simple wiki application.",
        "history": [{"timestamp": datetime.datetime.now().isoformat(), "content": "This is a simple wiki application."}]
    }
}


# Utility Functions
def page_exists(page_name):
    return page_name in wiki_pages

# API Routes
@app.route('/api/pages', methods=['GET'])
def list_pages():
    """Lists all available pages."""
    return jsonify(list(wiki_pages.keys()))


@app.route('/api/pages/<page_name>', methods=['GET'])
def get_page(page_name):
    """Retrieves a specific page by name."""
    if not page_exists(page_name):
        abort(404, description="Page not found")
    return jsonify(wiki_pages[page_name])


@app.route('/api/pages/<page_name>', methods=['POST'])
def create_page(page_name):
    """Creates a new page."""
    if page_exists(page_name):
        abort(400, description="Page already exists")

    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        abort(400, description="Title and content are required")

    wiki_pages[page_name] = {
        "title": data['title'],
        "content": data['content'],
        "history": [{"timestamp": datetime.datetime.now().isoformat(), "content": data['content']}]
    }
    return jsonify({"message": "Page created successfully"}), 201


@app.route('/api/pages/<page_name>', methods=['PUT'])
def update_page(page_name):
    """Updates an existing page."""
    if not page_exists(page_name):
        abort(404, description="Page not found")

    data = request.get_json()
    if not data or 'content' not in data:
        abort(400, description="Content is required")

    wiki_pages[page_name]["content"] = data['content']
    wiki_pages[page_name]["history"].append({"timestamp": datetime.datetime.now().isoformat(), "content": data['content']})

    return jsonify({"message": "Page updated successfully"})


@app.route('/api/pages/<page_name>', methods=['DELETE'])
def delete_page(page_name):
    """Deletes a page."""
    if not page_exists(page_name):
        abort(404, description="Page not found")

    del wiki_pages[page_name]
    return jsonify({"message": "Page deleted successfully"})


@app.route('/api/pages/<page_name>/history', methods=['GET'])
def get_page_history(page_name):
    """Retrieves the version history of a page."""
    if not page_exists(page_name):
        abort(404, description="Page not found")
    return jsonify(wiki_pages[page_name]["history"])


@app.route('/api/search', methods=['GET'])
def search_pages():
    """Searches for pages containing the given query."""
    query = request.args.get('q', '').lower()
    results = []
    for page_name, page_data in wiki_pages.items():
        if query in page_name.lower() or query in page_data["title"].lower() or query in page_data["content"].lower():
            results.append({"name": page_name, "title": page_data["title"]})
    return jsonify(results)


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": error.description}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": error.description}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5435')), debug=True)
