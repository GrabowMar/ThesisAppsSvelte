# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import difflib
import re
from sqlalchemy.sql import func

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wiki.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_change_in_production')

# 3. Database Setup
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 4. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    revisions = db.relationship('PageRevision', backref='page', lazy=True, cascade='all, delete-orphan')
    
    @property
    def current_content(self):
        latest = PageRevision.query.filter_by(page_id=self.id).order_by(PageRevision.created_at.desc()).first()
        return latest.content if latest else ""

class PageRevision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.Integer, db.ForeignKey('page.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    edit_summary = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
# Association table for many-to-many relationship between Page and Tag
page_tags = db.Table('page_tags',
    db.Column('page_id', db.Integer, db.ForeignKey('page.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

# 5. Utility Functions
def generate_slug(title):
    """Generate a URL-friendly slug from the title"""
    slug = title.lower()
    # Replace non-alphanumeric characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

def get_diff(old_content, new_content):
    """Generate a diff between two versions of content"""
    diff = difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        n=3
    )
    return ''.join(diff)

# Create tables
with app.app_context():
    db.create_all()
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin123')  # Change in production!
        db.session.add(admin)
        db.session.commit()

# 6. API Routes

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    
    # Validate input
    if not all(k in data for k in ['username', 'password', 'email']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create new user
    try:
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    
    if not all(k in data for k in ['username', 'password']):
        return jsonify({'error': 'Missing username or password'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # In a real app, you would generate a JWT token here
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

# Wiki page routes
@app.route('/api/pages', methods=['GET'])
def get_pages():
    """Get a list of all wiki pages"""
    pages = Page.query.all()
    result = []
    for page in pages:
        result.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'updated_at': page.updated_at.isoformat(),
            'created_at': page.created_at.isoformat()
        })
    return jsonify(result), 200

@app.route('/api/pages/search', methods=['GET'])
def search_pages():
    """Search wiki pages by title or content"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify({'error': 'Search query too short'}), 400
    
    # Search in titles and content
    matching_titles = Page.query.filter(Page.title.ilike(f'%{query}%')).all()
    
    # For content search, we need to check each page's latest revision
    content_matches = []
    all_pages = Page.query.all()
    for page in all_pages:
        if page not in matching_titles:  # Avoid duplicates
            latest_revision = PageRevision.query.filter_by(page_id=page.id).order_by(PageRevision.created_at.desc()).first()
            if latest_revision and query.lower() in latest_revision.content.lower():
                content_matches.append(page)
    
    results = []
    for page in matching_titles + content_matches:
        results.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'updated_at': page.updated_at.isoformat(),
            'match_type': 'title' if page in matching_titles else 'content'
        })
    
    return jsonify(results), 200

@app.route('/api/pages/<string:slug>', methods=['GET'])
def get_page(slug):
    """Get a specific wiki page by slug"""
    page = Page.query.filter_by(slug=slug).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    latest_revision = PageRevision.query.filter_by(page_id=page.id).order_by(PageRevision.created_at.desc()).first()
    
    return jsonify({
        'id': page.id,
        'title': page.title,
        'slug': page.slug,
        'content': latest_revision.content if latest_revision else "",
        'updated_at': page.updated_at.isoformat(),
        'created_at': page.created_at.isoformat()
    }), 200

@app.route('/api/pages', methods=['POST'])
def create_page():
    """Create a new wiki page"""
    data = request.json
    
    if not all(k in data for k in ['title', 'content']):
        return jsonify({'error': 'Missing title or content'}), 400
    
    # Check if page with this title already exists
    existing_page = Page.query.filter_by(title=data['title']).first()
    if existing_page:
        return jsonify({'error': 'Page with this title already exists'}), 400
    
    slug = generate_slug(data['title'])
    
    # Check if slug already exists
    if Page.query.filter_by(slug=slug).first():
        return jsonify({'error': 'Page with similar title already exists'}), 400
    
    try:
        # Create the page
        page = Page(title=data['title'], slug=slug)
        db.session.add(page)
        db.session.flush()  # Get the page id
        
        # Create the initial revision
        revision = PageRevision(
            page_id=page.id,
            content=data['content'],
            edit_summary='Initial version',
            user_id=data.get('user_id')  # Optional
        )
        db.session.add(revision)
        
        # Handle tags if provided
        if 'tags' in data and isinstance(data['tags'], list):
            for tag_name in data['tags']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                page.tags.append(tag)
        
        db.session.commit()
        return jsonify({
            'message': 'Page created successfully',
            'page': {
                'id': page.id,
                'title': page.title,
                'slug': page.slug
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pages/<string:slug>', methods=['PUT'])
def update_page(slug):
    """Update an existing wiki page"""
    data = request.json
    
    if 'content' not in data:
        return jsonify({'error': 'Content is required'}), 400
    
    page = Page.query.filter_by(slug=slug).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    try:
        # Get the latest revision to compare
        latest_revision = PageRevision.query.filter_by(page_id=page.id).order_by(PageRevision.created_at.desc()).first()
        old_content = latest_revision.content if latest_revision else ""
        
        # Update page title if provided
        if 'title' in data and data['title'] != page.title:
            # Check if new title already exists
            existing_page = Page.query.filter_by(title=data['title']).first()
            if existing_page and existing_page.id != page.id:
                return jsonify({'error': 'Page with this title already exists'}), 400
            
            # Update title and slug
            page.title = data['title']
            page.slug = generate_slug(data['title'])
        
        # Create a new revision
        revision = PageRevision(
            page_id=page.id,
            content=data['content'],
            edit_summary=data.get('edit_summary', 'Updated content'),
            user_id=data.get('user_id')
        )
        db.session.add(revision)
        
        # Update the page's updated_at timestamp
        page.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Page updated successfully',
            'page': {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'diff': get_diff(old_content, data['content'])
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pages/<string:slug>', methods=['DELETE'])
def delete_page(slug):
    """Delete a wiki page"""
    page = Page.query.filter_by(slug=slug).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    try:
        db.session.delete(page)
        db.session.commit()
        return jsonify({'message': 'Page deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pages/<string:slug>/revisions', methods=['GET'])
def get_page_revisions(slug):
    """Get the revision history of a page"""
    page = Page.query.filter_by(slug=slug).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    revisions = PageRevision.query.filter_by(page_id=page.id).order_by(PageRevision.created_at.desc()).all()
    
    result = []
    for rev in revisions:
        result.append({
            'id': rev.id,
            'edit_summary': rev.edit_summary,
            'created_at': rev.created_at.isoformat(),
            'user': rev.user.username if rev.user else None
        })
    
    return jsonify(result), 200

@app.route('/api/pages/<string:slug>/revisions/<int:revision_id>', methods=['GET'])
def get_page_revision(slug, revision_id):
    """Get a specific revision of a page"""
    page = Page.query.filter_by(slug=slug).first()
    if not page:
        return jsonify({'error': 'Page not found'}), 404
    
    revision = PageRevision.query.filter_by(id=revision_id, page_id=page.id).first()
    if not revision:
        return jsonify({'error': 'Revision not found'}), 404
    
    return jsonify({
        'id': revision.id,
        'content': revision.content,
        'edit_summary': revision.edit_summary,
        'created_at': revision.created_at.isoformat(),
        'user': revision.user.username if revision.user else None
    }), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5355')))
