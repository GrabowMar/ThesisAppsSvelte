# app.py

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory data store (replace with a database in production)
users = {}
rooms = {"general": []}

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username in users:
        return jsonify({"error": "Username already exists"}), 400
    users[username] = {
        "password": generate_password_hash(password),
        "online": False
    }
    return jsonify({"message": "Registration successful"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username not in users or not check_password_hash(users[username]["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    session['username'] = username
    users[username]["online"] = True
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    username = session.get('username')
    if username:
        users[username]["online"] = False
        session.pop('username', None)
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    return jsonify(list(rooms.keys())), 200

@app.route('/api/room/<room_name>/messages', methods=['GET'])
def get_room_messages(room_name):
    if room_name not in rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify(rooms[room_name]), 200

@app.route('/api/room/<room_name>/join', methods=['POST'])
def join_room_api(room_name):
    username = session.get('username')
    if not username:
        return jsonify({"error": "Not logged in"}), 401
    if room_name not in rooms:
        rooms[room_name] = []
    if username not in rooms[room_name]:
        rooms[room_name].append(username)
    return jsonify({"message": f"Joined {room_name}"}), 200

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = session.get('username')
    if username and room in rooms and username in rooms[room]:
        socketio.emit('message', {'username': username, 'message': message, 'room': room}, room=room)

@socketio.on('join')
def on_join(data):
    username = session.get('username')
    room = data['room']
    join_room(room)
    socketio.emit('status', {'msg': f'{username} has entered the room.', 'room': room}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = session.get('username')
    room = data['room']
    leave_room(room)
    socketio.emit('status', {'msg': f'{username} has left the room.', 'room': room}, room=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5483')))
