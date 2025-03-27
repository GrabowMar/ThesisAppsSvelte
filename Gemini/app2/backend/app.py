# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'  # Change in production
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Data Structures (Emulating Database)
users = {}  # {user_id: {username, online, room}}
messages = {} # {room_id: [{user_id, username, content, timestamp}]}
rooms = {'general': {'name': 'General Chat', 'description': 'General discussion room'}} # {room_id: {name, description}}

# 4. Authentication Logic (Simple example - expand as needed)
def create_user(username):
    user_id = str(uuid.uuid4())
    users[user_id] = {'username': username, 'online': True, 'room': 'general'}
    return user_id

# 5. Utility Functions

def get_room_messages(room_id):
    return messages.get(room_id, [])

def add_message(room_id, user_id, username, content):
    if room_id not in messages:
        messages[room_id] = []
    messages[room_id].append({'user_id': user_id, 'username': username, 'content': content, 'timestamp':  datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required'}), 400

    user_id = create_user(username)  # In a real app, check if user exists
    return jsonify({'user_id': user_id, 'username': username})


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
  room_list = [{'id': room_id, 'name': room['name'], 'description': room['description']} for room_id, room in rooms.items()]
  return jsonify(room_list)

@app.route('/api/messages/<room_id>', methods=['GET'])
def get_messages(room_id):
    if room_id in messages:
        return jsonify(messages[room_id])
    else:
        return jsonify([])

# 7. SocketIO Events

from datetime import datetime

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join_room(data):
    user_id = data.get('user_id')
    room_id = data.get('room_id')

    if user_id in users and room_id in rooms:
        leave_room(users[user_id]['room'])
        users[user_id]['room'] = room_id
        join_room(room_id)

        emit('user_joined', {'user_id': user_id, 'room_id': room_id}, room=room_id)
        print(f"User {user_id} joined room {room_id}")
    else:
        print(f"Invalid user_id or room_id: user_id={user_id}, room_id={room_id}")


@socketio.on('send_message')
def handle_send_message(data):
    user_id = data.get('user_id')
    room_id = data.get('room_id')
    content = data.get('content')

    if user_id in users:
        username = users[user_id]['username']
        add_message(room_id, user_id, username, content)
        emit('receive_message', {'user_id': user_id, 'username': username, 'content': content, 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, room=room_id)
    else:
        print(f"Invalid user_id: {user_id}")

# 8. Error Handlers (Example)
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5403')), debug=True)
