from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import uuid
from datetime import datetime
import eventlet
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env file (if present)
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-secret-key')
CORS(app, supports_credentials=True, resources={r"/*": {"origins": f"http://localhost:5823"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=f"http://localhost:5823", async_mode='eventlet')

# In-memory data storage
users = {}  # {username: {password: hashed_password, user_id: unique_id}}
active_users = {}  # {session_id: {username, user_id, rooms: []}}
rooms = {
    'general': {
        'name': 'General',
        'messages': []
    },
    'support': {
        'name': 'Support',
        'messages': []
    },
    'random': {
        'name': 'Random',
        'messages': []
    }
}

# Message history (limited to last 100 messages per room)
MAX_MESSAGES = 100

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    print(f"Error: {str(e)}")
    return jsonify({"status": "error", "message": str(e)}), 500

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({"status": "error", "message": "Username and password are required"}), 400
            
        if username in users:
            return jsonify({"status": "error", "message": "Username already exists"}), 409
            
        # Store new user
        users[username] = {
            'password': generate_password_hash(password),
            'user_id': str(uuid.uuid4())
        }
        
        return jsonify({"status": "success", "message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate credentials
        if username not in users:
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
            
        if not check_password_hash(users[username]['password'], password):
            return jsonify({"status": "error", "message": "Invalid credentials"}), 401
            
        # Generate session ID
        session_id = str(uuid.uuid4())
        user_id = users[username]['user_id']
        
        # Store in active users
        active_users[session_id] = {
            'username': username,
            'user_id': user_id,
            'rooms': ['general']  # Default room
        }
        
        return jsonify({
            "status": "success", 
            "session_id": session_id,
            "user_id": user_id,
            "username": username
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session_id = request.json.get('session_id')
        
        if session_id in active_users:
            # Remove user from all rooms
            for room in active_users[session_id]['rooms']:
                leave_room(room)
                
            # Notify others
            for room in active_users[session_id]['rooms']:
                socketio.emit('user_offline', {
                    'username': active_users[session_id]['username'],
                    'user_id': active_users[session_id]['user_id']
                }, room=room)
                
            # Remove from active users
            del active_users[session_id]
            
        return jsonify({"status": "success", "message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Status/authentication check
@app.route('/api/check-auth', methods=['POST'])
def check_auth():
    try:
        session_id = request.json.get('session_id')
        
        if session_id in active_users:
            return jsonify({
                "status": "success",
                "authenticated": True,
                "username": active_users[session_id]['username'],
                "user_id": active_users[session_id]['user_id']
            }), 200
        else:
            return jsonify({"status": "success", "authenticated": False}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Room management
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    return jsonify({
        "status": "success",
        "rooms": [{"id": room_id, "name": room_data["name"]} for room_id, room_data in rooms.items()]
    }), 200

@app.route('/api/rooms/create', methods=['POST'])
def create_room():
    try:
        data = request.json
        session_id = data.get('session_id')
        room_id = data.get('room_id', '').strip().lower().replace(' ', '-')
        room_name = data.get('room_name', '').strip()
        
        # Validate
        if session_id not in active_users:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        if not room_id or not room_name:
            return jsonify({"status": "error", "message": "Room ID and name are required"}), 400
            
        if room_id in rooms:
            return jsonify({"status": "error", "message": "Room ID already exists"}), 409
            
        # Create new room
        rooms[room_id] = {
            'name': room_name,
            'messages': []
        }
        
        # Broadcast new room to all users
        socketio.emit('room_added', {
            'id': room_id,
            'name': room_name
        })
        
        return jsonify({"status": "success", "message": "Room created", "room_id": room_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/rooms/<room_id>/messages', methods=['GET'])
def get_room_messages(room_id):
    try:
        session_id = request.args.get('session_id')
        
        # Validate
        if session_id not in active_users:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
            
        if room_id not in rooms:
            return jsonify({"status": "error", "message": "Room not found"}), 404
            
        return jsonify({
            "status": "success",
            "messages": rooms[room_id]['messages']
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Socket.IO event handlers
@socketio.on('connect')
def on_connect():
    session_id = request.args.get('session_id')
    
    if not session_id or session_id not in active_users:
        return False  # Reject connection
        
    print(f"User connected: {active_users[session_id]['username']}")

@socketio.on('join')
def on_join(data):
    session_id = data.get('session_id')
    room_id = data.get('room_id')
    
    if session_id not in active_users or room_id not in rooms:
        return
        
    # Add room to user's rooms if not already there
    if room_id not in active_users[session_id]['rooms']:
        active_users[session_id]['rooms'].append(room_id)
        
    # Join the room
    join_room(room_id)
    
    # Get user info
    username = active_users[session_id]['username']
    user_id = active_users[session_id]['user_id']
    
    # Notify room about new user
    emit('user_joined', {
        'username': username,
        'user_id': user_id,
        'room_id': room_id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)
    
    # Get active users in this room
    room_users = []
    for sid, user_data in active_users.items():
        if room_id in user_data['rooms']:
            room_users.append({
                'username': user_data['username'],
                'user_id': user_data['user_id']
            })
    
    # Send active users to the joined user
    emit('active_users', {
        'room_id': room_id,
        'users': room_users
    })

@socketio.on('leave')
def on_leave(data):
    session_id = data.get('session_id')
    room_id = data.get('room_id')
    
    if session_id not in active_users or room_id not in rooms:
        return
        
    # Remove room from user's rooms
    if room_id in active_users[session_id]['rooms']:
        active_users[session_id]['rooms'].remove(room_id)
        
    # Leave the room
    leave_room(room_id)
    
    # Get user info
    username = active_users[session_id]['username']
    user_id = active_users[session_id]['user_id']
    
    # Notify room about user leaving
    emit('user_left', {
        'username': username,
        'user_id': user_id,
        'room_id': room_id,
        'timestamp': datetime.now().isoformat()
    }, room=room_id)

@socketio.on('message')
def on_message(data):
    session_id = data.get('session_id')
    room_id = data.get('room_id')
    content = data.get('message', '').strip()
    
    if not content or session_id not in active_users or room_id not in rooms:
        return
        
    if room_id not in active_users[session_id]['rooms']:
        # Auto-join the room if not already joined
        join_room(room_id)
        active_users[session_id]['rooms'].append(room_id)
    
    # Create message object
    username = active_users[session_id]['username']
    user_id = active_users[session_id]['user_id']
    timestamp = datetime.now().isoformat()
    
    message = {
        'id': str(uuid.uuid4()),
        'room_id': room_id,
        'content': content,
        'username': username,
        'user_id': user_id,
        'timestamp': timestamp
    }
    
    # Store message in room history (limiting to MAX_MESSAGES)
    rooms[room_id]['messages'].append(message)
    if len(rooms[room_id]['messages']) > MAX_MESSAGES:
        rooms[room_id]['messages'] = rooms[room_id]['messages'][-MAX_MESSAGES:]
    
    # Broadcast to room
    emit('message', message, room=room_id)

@socketio.on('typing')
def on_typing(data):
    session_id = data.get('session_id')
    room_id = data.get('room_id')
    is_typing = data.get('is_typing', False)
    
    if session_id not in active_users or room_id not in rooms:
        return
        
    # Get user info
    username = active_users[session_id]['username']
    user_id = active_users[session_id]['user_id']
    
    # Broadcast typing status to room (except sender)
    emit('user_typing', {
        'username': username,
        'user_id': user_id,
        'is_typing': is_typing,
        'room_id': room_id
    }, room=room_id, include_self=False)

@socketio.on('disconnect')
def on_disconnect():
    # Find the session ID for this connection
    session_id = request.args.get('session_id')
    
    if session_id and session_id in active_users:
        username = active_users[session_id]['username']
        user_id = active_users[session_id]['user_id']
        user_rooms = active_users[session_id]['rooms'].copy()
        
        # Notify all rooms the user was in
        for room_id in user_rooms:
            emit('user_offline', {
                'username': username,
                'user_id': user_id,
                'room_id': room_id,
                'timestamp': datetime.now().isoformat()
            }, room=room_id)
            
            # Leave room
            leave_room(room_id)
            
        print(f"User disconnected: {username}")
        
        # User remains in active_users until explicit logout
        # This allows reconnection with the same session ID

if __name__ == '__main__':
    print(f"Starting Flask SocketIO server on port 5323...")
    socketio.run(app, host='0.0.0.0', port=5323, debug=True)