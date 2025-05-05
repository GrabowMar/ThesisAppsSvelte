from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

# App Configuration
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Database Models (if needed)
# Example:
# from models import User, Message

# Authentication Logic (if needed)
# Example:
# @app.route('/login', methods=['POST'])
# def login():
#     # Authentication logic here
#     pass

# Utility Functions
# Example:
# def get_user(user_id):
#     # Fetch user logic here
#     pass

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    # Registration logic here
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # Login logic here
    return jsonify({"message": "User logged in successfully"}), 200

@app.route('/api/messages', methods=['GET'])
def get_messages():
    # Fetch messages logic here
    return jsonify({"messages": []}), 200

# SocketIO Events
@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    emit('status', {'msg': username + ' has entered the room.'}, room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    emit('status', {'msg': username + ' has left the room.'}, room=room)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5083')))
