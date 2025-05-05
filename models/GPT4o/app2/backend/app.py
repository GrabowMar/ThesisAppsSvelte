from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
CORS(app)

# Socket initialization for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Example data store for chat messages and users
users = []  # List of online users
chat_rooms = {"public": []}  # One default public chat room

@app.route('/api/users', methods=['GET'])
def get_users():
    """Retrieve all online users."""
    return jsonify({"users": users}), 200

@app.route('/api/chat_rooms', methods=['GET'])
def get_chat_rooms():
    """Retrieve chat rooms."""
    return jsonify({"chat_rooms": list(chat_rooms.keys())}), 200

@app.route('/api/history/<room>', methods=['GET'])
def get_chat_history(room):
    """Retrieve chat history for a specific room."""
    if room not in chat_rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"messages": chat_rooms[room]}), 200

@socketio.on('join')
def on_join(data):
    """Handle users joining a chat room."""
    username = data.get("username")
    room = data.get("room", "public")
    if room not in chat_rooms:
        chat_rooms[room] = []
    if username not in users:
        users.append(username)  # Add user to the online list
    emit('status', {"message": f"{username} joined {room}."}, broadcast=True)

@socketio.on('send_message')
def on_message(data):
    """Handle sending messages in a chat room."""
    message = data.get("message")
    username = data.get("username")
    room = data.get("room", "public")
    if room not in chat_rooms:
        return {"error": "Room not found"}
    chat_message = {"username": username, "message": message}
    chat_rooms[room].append(chat_message)
    emit('receive_message', chat_message, broadcast=True)

@socketio.on('disconnect')
def on_disconnect():
    """Handle when a user disconnects."""
    # This would require user tracking logic
    pass

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5243')))