from flask import Flask, jsonify, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from datetime import datetime
import jwt
import secrets
from functools import wraps

# App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(16))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///chat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions setup
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    online = db.Column(db.Boolean, default=False)
    messages = db.relationship('Message', backref='author', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='room', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)

# Create all tables
with app.app_context():
    db.create_all()
    # Create a general room if it doesn't exist
    if not Room.query.filter_by(name="General").first():
        general_room = Room(name="General")
        db.session.add(general_room)
        db.session.commit()

# Auth utility functions and decorators
def generate_token(user_id):
    """Generate JWT token for authenticated users"""
    return jwt.encode(
        {'user_id': user_id},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def token_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Socket connection handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # If we have user_id in session, update online status
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.online = False
            db.session.commit()
            emit('user_status', {'user_id': user.id, 'username': user.username, 'online': False}, broadcast=True)

@socketio.on('join')
def on_join(data):
    """User joins a room"""
    room = data['room']
    username = data.get('username', 'Anonymous')
    user_id = data.get('user_id')
    
    # Store in session for disconnect handling
    if user_id:
        session['user_id'] = user_id
        user = User.query.get(user_id)
        if user:
            user.online = True
            db.session.commit()
            emit('user_status', {'user_id': user.id, 'username': user.username, 'online': True}, broadcast=True)
    
    join_room(room)
    emit('message', {
        'user': 'system',
        'content': f'{username} has joined the room.',
        'timestamp': datetime.utcnow().isoformat(),
        'room': room
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    """User leaves a room"""
    room = data['room']
    username = data.get('username', 'Anonymous')
    
    leave_room(room)
    emit('message', {
        'user': 'system',
        'content': f'{username} has left the room.',
        'timestamp': datetime.utcnow().isoformat(),
        'room': room
    }, room=room)

@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages"""
    room_name = data['room']
    user_id = data['user_id']
    content = data['message']
    
    # Save message to database
    try:
        user = User.query.get(user_id)
        room = Room.query.filter_by(name=room_name).first()
        
        if user and room:
            message = Message(content=content, user_id=user_id, room_id=room.id)
            db.session.add(message)
            db.session.commit()
            
            # Broadcast the message to everyone in the room
            emit('message', {
                'id': message.id,
                'user': user.username,
                'user_id': user.id,
                'content': content,
                'timestamp': message.timestamp.isoformat(),
                'room': room_name
            }, room=room_name)
    except Exception as e:
        print(f"Error saving message: {str(e)}")
        emit('error', {'message': 'Failed to save message'}, room=request.sid)

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        token = generate_token(new_user.id)
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': new_user.id,
                'username': new_user.username
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password'}), 401
    
    user.online = True
    db.session.commit()
    
    token = generate_token(user.id)
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username
        }
    }), 200

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(current_user):
    """User logout"""
    current_user.online = False
    db.session.commit()
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/rooms', methods=['GET'])
@token_required
def get_rooms(current_user):
    """Get all available chat rooms"""
    rooms = Room.query.all()
    return jsonify({
        'rooms': [{'id': room.id, 'name': room.name} for room in rooms]
    }), 200

@app.route('/api/rooms', methods=['POST'])
@token_required
def create_room(current_user):
    """Create a new chat room"""
    data = request.json
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Room name is required'}), 400
    
    if Room.query.filter_by(name=data['name']).first():
        return jsonify({'message': 'Room already exists'}), 409
    
    new_room = Room(name=data['name'])
    
    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({
            'message': 'Room created successfully',
            'room': {
                'id': new_room.id,
                'name': new_room.name
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Failed to create room', 'error': str(e)}), 500

@app.route('/api/rooms/<int:room_id>/messages', methods=['GET'])
@token_required
def get_room_messages(current_user, room_id):
    """Get message history for a specific room"""
    room = Room.query.get(room_id)
    
    if not room:
        return jsonify({'message': 'Room not found'}), 404
    
    # Get messages with a limit (e.g., most recent 100)
    messages = (Message.query
                .filter_by(room_id=room_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    
    # Reverse to get chronological order
    messages.reverse()
    
    return jsonify({
        'room': room.name,
        'messages': [{
            'id': msg.id,
            'content': msg.content,
            'user_id': msg.user_id,
            'user': msg.author.username,
            'timestamp': msg.timestamp.isoformat()
        } for msg in messages]
    }), 200

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    """Get all users and their online status"""
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'online': user.online
        } for user in users]
    }), 200

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get current user's profile"""
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
        }
    }), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5323')), debug=True)