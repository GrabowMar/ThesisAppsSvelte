# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')

# 3. Database Models (if needed)
# For simplicity, we'll use a dictionary to store user data
users = {}
rooms = {}

# 4. Authentication Logic (if needed)
# Simple authentication using username and password
def authenticate(username, password):
    if username in users and users[username]['password'] == password:
        return True
    return False

# 5. Utility Functions
def get_user_id(username):
    return username

# 6. API Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    if authenticate(username, password):
        user_id = get_user_id(username)
        return jsonify({'user_id': user_id})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']
    if username not in users:
        users[username] = {'password': password, 'rooms': []}
        return jsonify({'user_id': get_user_id(username)})
    return jsonify({'error': 'Username already taken'}), 400

# 7. SocketIO Events
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data['room_id']
    user_id = data['user_id']
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(user_id)
    emit('joined_room', {'room_id': room_id}, broadcast=True)

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data['room_id']
    user_id = data['user_id']
    if room_id in rooms and user_id in rooms[room_id]:
        rooms[room_id].remove(user_id)
    emit('left_room', {'room_id': room_id}, broadcast=True)

@socketio.on('send_message')
def handle_send_message(data):
    room_id = data['room_id']
    message = data['message']
    emit('new_message', {'room_id': room_id, 'message': message}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5003')))
