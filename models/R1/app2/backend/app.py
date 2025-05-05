# 1. Imports Section
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development-secret')
socketio = SocketIO(app, cors_allowed_origins="*")

# 3. Database Models (In-memory storage for simplicity)
users = {}
rooms = {
    'general': {'messages': [], 'members': set()},
    'random': {'messages': [], 'members': set()}
}

# 4. Utility Functions
def get_user_list(room):
    return [{'id': uid, 'username': users[uid]} for uid in rooms[room]['members']]

# 5. WebSocket Handlers
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid
    if user_id in users:
        username = users[user_id]
        for room in rooms.values():
            if user_id in room['members']:
                room['members'].remove(user_id)
        del users[user_id]
        emit('user_left', {'username': username}, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    room = data['room']
    username = data['username']
    user_id = request.sid
    
    users[user_id] = username
    join_room(room)
    rooms[room]['members'].add(user_id)
    
    # Send room info to user
    emit('room_history', {
        'messages': rooms[room]['messages'][-100:],
        'users': get_user_list(room)
    })
    
    # Notify others
    emit('user_joined', {
        'username': username,
        'timestamp': datetime.now().isoformat(),
        'users': get_user_list(room)
    }, to=room)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = {
        'id': len(rooms[room]['messages']),
        'username': users[request.sid],
        'content': data['content'],
        'timestamp': datetime.now().isoformat()
    }
    rooms[room]['messages'].append(message)
    emit('new_message', message, to=room)

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5563')), allow_unsafe_werkzeug=True)
