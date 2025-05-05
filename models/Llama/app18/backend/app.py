# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wiki.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    page = db.relationship('Page', backref=db.backref('versions', lazy=True))
    content = db.Column(db.Text, nullable=False)

# 4. Authentication Logic (if needed)
# For this example, we won't include authentication

# 5. Utility Functions
def page_to_dict(page):
    return {
        'id': page.id,
        'title': page.title,
        'content': page.content
    }

def version_to_dict(version):
    return {
        'id': version.id,
        'page_id': version.page_id,
        'content': version.content
    }

# 6. API Routes
@app.route('/api/pages', methods=['GET'])
def get_pages():
    pages = Page.query.all()
    return jsonify([page_to_dict(page) for page in pages])

@app.route('/api/pages/<int:page_id>', methods=['GET'])
def get_page(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return jsonify({'error': 'Page not found'}), 404
    return jsonify(page_to_dict(page))

@app.route('/api/pages', methods=['POST'])
def create_page():
    data = request.get_json()
    page = Page(title=data['title'], content=data['content'])
    db.session.add(page)
    db.session.commit()
    return jsonify(page_to_dict(page))

@app.route('/api/pages/<int:page_id>', methods=['PUT'])
def update_page(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return jsonify({'error': 'Page not found'}), 404
    data = request.get_json()
    page.title = data['title']
    page.content = data['content']
    db.session.commit()
    return jsonify(page_to_dict(page))

@app.route('/api/pages/<int:page_id>', methods=['DELETE'])
def delete_page(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return jsonify({'error': 'Page not found'}), 404
    db.session.delete(page)
    db.session.commit()
    return jsonify({'message': 'Page deleted'})

@app.route('/api/versions', methods=['GET'])
def get_versions():
    versions = Version.query.all()
    return jsonify([version_to_dict(version) for version in versions])

@app.route('/api/versions/<int:version_id>', methods=['GET'])
def get_version(version_id):
    version = Version.query.get(version_id)
    if version is None:
        return jsonify({'error': 'Version not found'}), 404
    return jsonify(version_to_dict(version))

@app.route('/api/pages/<int:page_id>/versions', methods=['POST'])
def create_version(page_id):
    page = Page.query.get(page_id)
    if page is None:
        return jsonify({'error': 'Page not found'}), 404
    data = request.get_json()
    version = Version(page_id=page_id, content=data['content'])
    db.session.add(version)
    db.session.commit()
    return jsonify(version_to_dict(version))

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('query')
    pages = Page.query.filter(Page.title.like(f'%{query}%')).all()
    return jsonify([page_to_dict(page) for page in pages])

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5035')))
