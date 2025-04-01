# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
import jwt

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# 4. Authentication Logic
def generate_token(user):
    return jwt.encode({'user_id': user.id}, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(payload['user_id'])
    except:
        return None

# 5. Utility Functions
def paginate_results(results, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return results[start:end]

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = generate_token(user)
        return jsonify({'token': token}), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'GET':
        user = verify_token(request.headers.get('Authorization', '').split(' ')[1])
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        archived = request.args.get('archived', 'false').lower() == 'true'
        
        query = Note.query.filter_by(user_id=user.id)
        
        if search:
            query = query.filter(Note.title.ilike(f'%{search}%') | Note.content.ilike(f'%{search}%'))
        if category:
            query = query.filter_by(category=category)
        if archived is not None:
            query = query.filter_by(is_archived=archived)
        
        notes = query.order_by(Note.updated_at.desc()).all()
        paginated_notes = paginate_results(notes, page, per_page)
        
        return jsonify({
            'notes': [note.to_dict() for note in paginated_notes],
            'total': len(notes),
            'page': page,
            'per_page': per_page
        }), 200
    
    elif request.method == 'POST':
        user = verify_token(request.headers.get('Authorization', '').split(' ')[1])
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
        
        data = request.json
        new_note = Note(
            title=data['title'],
            content=data['content'],
            category=data['category'],
            user_id=user.id
        )
        db.session.add(new_note)
        db.session.commit()
        
        return jsonify(new_note.to_dict()), 201

@app.route('/api/notes/<int:note_id>', methods=['GET', 'PUT', 'DELETE'])
def note(note_id):
    user = verify_token(request.headers.get('Authorization', '').split(' ')[1])
    if not user:
        return jsonify({'message': 'Invalid token'}), 401
    
    note = Note.query.get_or_404(note_id)
    if note.user_id != user.id:
        return jsonify({'message': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        return jsonify(note.to_dict()), 200
    
    elif request.method == 'PUT':
        data = request.json
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        note.category = data.get('category', note.category)
        note.is_archived = data.get('is_archived', note.is_archived)
        db.session.commit()
        return jsonify(note.to_dict()), 200
    
    elif request.method == 'DELETE':
        db.session.delete(note)
        db.session.commit()
        return jsonify({'message': 'Note deleted successfully'}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'message': 'Forbidden'}), 403

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

# Model methods
def to_dict(self):
    return {
        'id': self.id,
        'title': self.title,
        'content': self.content,
        'category': self.category,
        'created_at': self.created_at.isoformat(),
        'updated_at': self.updated_at.isoformat(),
        'is_archived': self.is_archived
    }

Note.to_dict = to_dict

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5991')))
