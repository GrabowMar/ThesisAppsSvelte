from flask import Flask, jsonify, request, redirect, url_for, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity (replace with a database in production)
pages = {}
versions = {}

@app.route('/')
def home():
    return redirect(url_for('get_page', title='Home'))

@app.route('/page/<title>', methods=['GET'])
def get_page(title):
    page = pages.get(title, {'title': title, 'content': '', 'history': []})
    return jsonify(page)

@app.route('/page/<title>', methods=['POST'])
def save_page(title):
    data = request.get_json()
    content = data.get('content', '')

    if title not in pages:
        pages[title] = {'title': title, 'content': content, 'history': []}
    else:
        pages[title]['content'] = content

    # Save version history
    pages[title]['history'].append(content)
    versions[title] = len(pages[title]['history'])  # Track version count

    return jsonify({'message': 'Page saved successfully'})

@app.route('/search', methods=['GET'])
def search_pages():
    query = request.args.get('q', '')
    results = [title for title in pages if query.lower() in title.lower()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5195, debug=True)
