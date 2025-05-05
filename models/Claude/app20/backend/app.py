# 1. Imports Section
from flask import Flask, jsonify, request, abort, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
from datetime import datetime
import json
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mapsharing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
db = SQLAlchemy(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    maps = db.relationship('Map', backref='owner', lazy=True)

class Map(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    markers = db.relationship('Marker', backref='map', lazy=True, cascade="all, delete-orphan")
    routes = db.relationship('Route', backref='map', lazy=True, cascade="all, delete-orphan")

class Marker(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(20), default='red')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    map_id = db.Column(db.String(36), db.ForeignKey('map.id'), nullable=False)

class Route(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    path = db.Column(db.Text, nullable=False)  # JSON string of coordinates
    color = db.Column(db.String(20), default='blue')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    map_id = db.Column(db.String(36), db.ForeignKey('map.id'), nullable=False)

# 4. Authentication Logic
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 5. Utility Functions
def create_db():
    with app.app_context():
        db.create_all()

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        id=str(uuid.uuid4()),
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    session['user_id'] = user.id
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logout successful'})

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@app.route('/api/maps', methods=['GET'])
def get_maps():
    if 'user_id' in session:
        user_maps = Map.query.filter_by(user_id=session['user_id']).all()
        public_maps = Map.query.filter_by(is_public=True).filter(Map.user_id != session['user_id']).all()
    else:
        user_maps = []
        public_maps = Map.query.filter_by(is_public=True).all()
    
    maps_data = {
        'user_maps': [{
            'id': map.id,
            'title': map.title,
            'description': map.description,
            'is_public': map.is_public,
            'created_at': map.created_at.isoformat(),
            'owner': map.owner.username
        } for map in user_maps],
        'public_maps': [{
            'id': map.id,
            'title': map.title,
            'description': map.description,
            'is_public': map.is_public,
            'created_at': map.created_at.isoformat(),
            'owner': map.owner.username
        } for map in public_maps]
    }
    
    return jsonify(maps_data)

@app.route('/api/maps', methods=['POST'])
@login_required
def create_map():
    data = request.get_json()
    
    if not data or not data.get('title'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_map = Map(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        is_public=data.get('is_public', True),
        user_id=session['user_id']
    )
    
    try:
        db.session.add(new_map)
        db.session.commit()
        return jsonify({
            'message': 'Map created successfully',
            'map': {
                'id': new_map.id,
                'title': new_map.title,
                'description': new_map.description,
                'is_public': new_map.is_public,
                'created_at': new_map.created_at.isoformat(),
                'owner': new_map.owner.username
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maps/<map_id>', methods=['GET'])
def get_map(map_id):
    map_data = Map.query.get(map_id)
    
    if not map_data:
        return jsonify({'error': 'Map not found'}), 404
    
    if not map_data.is_public and ('user_id' not in session or session['user_id'] != map_data.user_id):
        return jsonify({'error': 'You do not have permission to view this map'}), 403
    
    markers = [{
        'id': marker.id,
        'title': marker.title,
        'description': marker.description,
        'latitude': marker.latitude,
        'longitude': marker.longitude,
        'color': marker.color
    } for marker in map_data.markers]
    
    routes = [{
        'id': route.id,
        'title': route.title,
        'description': route.description,
        'path': json.loads(route.path),
        'color': route.color
    } for route in map_data.routes]
    
    return jsonify({
        'map': {
            'id': map_data.id,
            'title': map_data.title,
            'description': map_data.description,
            'is_public': map_data.is_public,
            'created_at': map_data.created_at.isoformat(),
            'owner': map_data.owner.username,
            'markers': markers,
            'routes': routes
        }
    })

@app.route('/api/maps/<map_id>', methods=['PUT'])
@login_required
def update_map(map_id):
    map_data = Map.query.get(map_id)
    
    if not map_data:
        return jsonify({'error': 'Map not found'}), 404
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to edit this map'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        map_data.title = data['title']
    if 'description' in data:
        map_data.description = data['description']
    if 'is_public' in data:
        map_data.is_public = data['is_public']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Map updated successfully',
            'map': {
                'id': map_data.id,
                'title': map_data.title,
                'description': map_data.description,
                'is_public': map_data.is_public
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maps/<map_id>', methods=['DELETE'])
@login_required
def delete_map(map_id):
    map_data = Map.query.get(map_id)
    
    if not map_data:
        return jsonify({'error': 'Map not found'}), 404
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to delete this map'}), 403
    
    try:
        db.session.delete(map_data)
        db.session.commit()
        return jsonify({'message': 'Map deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maps/<map_id>/markers', methods=['POST'])
@login_required
def add_marker(map_id):
    map_data = Map.query.get(map_id)
    
    if not map_data:
        return jsonify({'error': 'Map not found'}), 404
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to edit this map'}), 403
    
    data = request.get_json()
    
    if not data or 'title' not in data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    marker = Marker(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        latitude=data['latitude'],
        longitude=data['longitude'],
        color=data.get('color', 'red'),
        map_id=map_id
    )
    
    try:
        db.session.add(marker)
        db.session.commit()
        return jsonify({
            'message': 'Marker added successfully',
            'marker': {
                'id': marker.id,
                'title': marker.title,
                'description': marker.description,
                'latitude': marker.latitude,
                'longitude': marker.longitude,
                'color': marker.color
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maps/<map_id>/routes', methods=['POST'])
@login_required
def add_route(map_id):
    map_data = Map.query.get(map_id)
    
    if not map_data:
        return jsonify({'error': 'Map not found'}), 404
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to edit this map'}), 403
    
    data = request.get_json()
    
    if not data or 'title' not in data or 'path' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    route = Route(
        id=str(uuid.uuid4()),
        title=data['title'],
        description=data.get('description', ''),
        path=json.dumps(data['path']),
        color=data.get('color', 'blue'),
        map_id=map_id
    )
    
    try:
        db.session.add(route)
        db.session.commit()
        return jsonify({
            'message': 'Route added successfully',
            'route': {
                'id': route.id,
                'title': route.title,
                'description': route.description,
                'path': data['path'],
                'color': route.color
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/markers/<marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get(marker_id)
    
    if not marker:
        return jsonify({'error': 'Marker not found'}), 404
    
    map_data = Map.query.get(marker.map_id)
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to delete this marker'}), 403
    
    try:
        db.session.delete(marker)
        db.session.commit()
        return jsonify({'message': 'Marker deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/routes/<route_id>', methods=['DELETE'])
@login_required
def delete_route(route_id):
    route = Route.query.get(route_id)
    
    if not route:
        return jsonify({'error': 'Route not found'}), 404
    
    map_data = Map.query.get(route.map_id)
    
    if map_data.user_id != session['user_id']:
        return jsonify({'error': 'You do not have permission to delete this route'}), 403
    
    try:
        db.session.delete(route)
        db.session.commit()
        return jsonify({'message': 'Route deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Create database on startup if it doesn't exist
create_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5359')), debug=True)
