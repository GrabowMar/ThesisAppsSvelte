# app/backend/app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, leave_room, emit
import os
import eventlet

# Perform eventlet monkey patching for asynchronous support
eventlet.monkey_patch()

app = Flask(__name__, static_folder='../frontend')
CORS(app)
# Configure SocketIO for real-time messaging with CORS support.
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# In-memory chat rooms data store and online users management
chat_rooms = {"General": []}  # channel -> list of messages
online_users = {}  # socketID -> username

# -----------------------
# REST API Routes
# -----------------------

@app.route('/login', methods=['POST'])
def login():
    """
    Dummy login endpoint.
    Expected JSON: { "username": "user", "password": "pass" }
    In production, add proper authentication and error validation.
    """
    data = request.json
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Invalid credentials"}), 400

    # For now, just assume login is successful and return the username
    return jsonify({"message": "Login successful", "username": data["username"]})

@app.route('/register', methods=['POST'])
def register():
    """
    Dummy user register endpoint.
    Expected JSON: { "username": "user", "password": "pass"}.
    """
    data = request.json
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Invalid registration data"}), 400

    # In production, insert data into the database and handle duplicates.
    return jsonify({"message": "Registration successful", "username": data["username"]})

@app.route('/chat/history', methods=['GET'])
def chat_history():
    """
    Returns the chat message history for a room.
    Query parameter: room
    """
    room = request.args.get('room', 'General')
    if room not in chat_rooms:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"room": room, "messages": chat_rooms[room]})

# -----------------------
# SocketIO Real-Time Handlers
# -----------------------

@socketio.on('connect')
def handle_connect():
    print("Client connected:", request.sid)
    emit('connection_accepted', {'message': 'Connected to the SocketIO server.'})

@socketio.on('join')
def on_join(data):
    """
    Client should provide a username and room name.
    Example data: { "username": "JohnDoe", "room": "General" }
    """
    username = data.get('username')
    room = data.get('room', 'General')
    if not username:
        return emit('error', {'error': 'Username is required to join a room.'})

    join_room(room)
    online_users[request.sid] = username
    # Inform room members
    emit('status', {'message': f"{username} has joined {room}"}, room=room)
    # Send chat history so the client can catch up
    if room in chat_rooms:
        emit('chat_history', {"room": room, "messages": chat_rooms[room]})
    else:
        # Create room if not exist
        chat_rooms[room] = []
    print(f"{username} joined room: {room}")

@socketio.on('leave')
def on_leave(data):
    """
    Client can leave a specific room.
    Expected JSON: { "username": "JohnDoe", "room": "General" }
    """
    username = data.get('username')
    room = data.get('room', 'General')
    leave_room(room)
    if request.sid in online_users:
        del online_users[request.sid]
    emit('status', {'message': f"{username} has left {room}"}, room=room)
    print(f"{username} left room: {room}")

@socketio.on('message')
def handle_message(data):
    """
    Handles receiving a new message.
    Expected JSON: { "username": "JohnDoe", "room": "General", "message": "Hello!" }
    """
    username = data.get('username')
    room = data.get('room', 'General')
    message = data.get('message')
    if not username or not message:
        return emit('error', {'error': 'Username and message are required.'})
    
    new_message = {"username": username, "message": message}
    # Append the new message to room history
    if room not in chat_rooms:
        chat_rooms[room] = []
    chat_rooms[room].append(new_message)
    # Broadcast message to room members
    emit('message', new_message, room=room)
    print(f"Message from {username} in {room}: {message}")

@socketio.on('disconnect')
def test_disconnect():
    """
    Disconnect event handler.
    """
    username = online_users.get(request.sid, "Unknown")
    print("Client disconnected:", request.sid, username)
    # Optionally, broadcast the user left message to all rooms if needed.
    if request.sid in online_users:
        del online_users[request.sid]

# -----------------------
# Error Handlers
# -----------------------

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server encountered an error"}), 500

# -----------------------
# Serve Frontend (if needed)
# -----------------------
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """
    In production, the frontend build could be served by Flask.
    This example assumes the index.html is in ../frontend.
    """
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

# -----------------------
# Main Execution
# -----------------------
if __name__ == '__main__':
    port = int(os.getenv('PORT', '6143'))  # Backend on port 6143
    print("Starting Flask-SocketIO on port", port)
    socketio.run(app, host='0.0.0.0', port=port)
