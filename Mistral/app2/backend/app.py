from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# In-memory storage for simplicity
users = {}
messages = {}
online_users = set()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    if username:
        users[username] = {'status': 'offline'}
        session['username'] = username
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Username required'}), 400

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    if username:
        users[username] = {'status': 'offline'}
        return jsonify({'message': 'Registration successful'}), 200
    return jsonify({'message': 'Username required'}), 400

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'username' in session:
        return jsonify({'message': 'Welcome to the dashboard', 'username': session['username']}), 200
    return jsonify({'message': 'Unauthorized'}), 401

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        users[username]['status'] = 'online'
        online_users.add(username)
        emit('user_connected', {'username': username}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        users[username]['status'] = 'offline'
        online_users.discard(username)
        emit('user_disconnected', {'username': username}, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    username = session.get('username')
    room = data['room']
    join_room(room)
    if room not in messages:
        messages[room] = []
    emit('room_joined', {'username': username, 'room': room}, room=room)

@socketio.on('leave_room')
def handle_leave_room(data):
    username = session.get('username')
    room = data['room']
    leave_room(room)
    emit('room_left', {'username': username, 'room': room}, room=room)

@socketio.on('send_message')
def handle_send_message(data):
    username = session.get('username')
    room = data['room']
    message = data['message']
    messages[room].append({'username': username, 'message': message})
    emit('new_message', {'username': username, 'message': message}, room=room)

@app.route('/messages/<room>', methods=['GET'])
def get_messages(room):
    if room in messages:
        return jsonify(messages[room]), 200
    return jsonify({'message': 'No messages found'}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5083)
