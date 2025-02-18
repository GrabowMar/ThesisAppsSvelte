from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room, send
from flask_cors import CORS
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
CORS(app, supports_credentials=True)

users = {}
rooms = {"general": []}  # Default chat room

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if username in users:
        return jsonify({"error": "User already exists"}), 409
    users[username] = password
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if users.get(username) == password:
        session['username'] = username
        return jsonify({"message": "Login successful", "username": username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/rooms', methods=['GET'])
def get_rooms():
    return jsonify(list(rooms.keys()))

@app.route('/rooms', methods=['POST'])
def create_room():
    data = request.json
    room_name = data.get('room')
    if room_name in rooms:
        return jsonify({"error": "Room already exists"}), 409
    rooms[room_name] = []
    return jsonify({"message": "Room created"}), 201

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    rooms[room].append(username)
    send(f"{username} has joined {room}", to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    rooms[room].remove(username)
    send(f"{username} has left {room}", to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    message = data['message']
    username = data['username']
    send({"username": username, "message": message}, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5003, debug=True)