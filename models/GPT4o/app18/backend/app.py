from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Mock "in-memory" storage for simplicity
wiki_pages = {}
version_history = {}

# Default route
@app.route('/')
def welcome():
    return jsonify({"message": "Welcome to the Wiki API"}), 200


# Route to create or update a page
@app.route('/api/page', methods=['POST'])
def create_or_update_page():
    data = request.json
    page_name = data.get('name')
    content = data.get('content')

    if not page_name or not content:
        return jsonify({"error": "Missing 'name' or 'content'"}), 400

    # Versioning
    if page_name in wiki_pages:
        if page_name not in version_history:
            version_history[page_name] = []
        version_history[page_name].append(wiki_pages[page_name])

    wiki_pages[page_name] = content
    return jsonify({"message": f"Page '{page_name}' created/updated successfully!"}), 201


# Route to get a specific page
@app.route('/api/page/<string:page_name>', methods=['GET'])
def get_page(page_name):
    content = wiki_pages.get(page_name)
    if content:
        return jsonify({"name": page_name, "content": content}), 200
    return jsonify({"error": "Page not found"}), 404


# Route to search pages by name
@app.route('/api/search', methods=['GET'])
def search_pages():
    query = request.args.get('q', "").lower()
    results = {name: content for name, content in wiki_pages.items() if query in name.lower()}
    return jsonify(results), 200


# Route to get version history of a page
@app.route('/api/page/<string:page_name>/history', methods=['GET'])
def get_version_history(page_name):
    history = version_history.get(page_name, [])
    return jsonify({page_name: history}), 200


# Error Handler
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


# Run the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5275')))
