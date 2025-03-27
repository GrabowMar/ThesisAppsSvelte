# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wiki.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Version(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

# 4. Authentication Logic

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)

# 5. Utility Functions

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = hash_password(data['password'])
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password(user.password, data['password']):
        return jsonify({'message': 'Logged in successfully', 'user_id': user.id}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/pages', methods=['GET'])
def get_pages():
    pages = Page.query.all()
    return jsonify([{'id': page.id, 'title': page.title} for page in pages])

@app.route('/api/pages/<int:page_id>', methods=['GET'])
def get_page(page_id):
    page = Page.query.get(page_id)
    if page:
        return jsonify({'id': page.id, 'title': page.title, 'content': page.content})
    return jsonify({'message': 'Page not found'}), 404

@app.route('/api/pages', methods=['POST'])
def create_page():
    data = request.get_json()
    new_page = Page(title=data['title'], content=data['content'], author_id=data['author_id'])
    db.session.add(new_page)
    db.session.commit()
    return jsonify({'message': 'Page created successfully', 'page_id': new_page.id}), 201

@app.route('/api/pages/<int:page_id>', methods=['PUT'])
def edit_page(page_id):
    data = request.get_json()
    page = Page.query.get(page_id)
    if page:
        page.title = data['title']
        page.content = data['content']
        db.session.commit()
        return jsonify({'message': 'Page updated successfully'}), 200
    return jsonify({'message': 'Page not found'}), 404

@app.route('/api/pages/<int:page_id>/history', methods=['GET'])
def get_version_history(page_id):
    versions = Version.query.filter_by(page_id=page_id).all()
    return jsonify([{'version_number': version.version_number, 'content': version.content, 'timestamp': version.timestamp} for version in versions])

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5115')))
