from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app)

# In-memory storage for users and messages
users = {}
messages = {}

# Register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    if username in users:
        return jsonify({'error': 'Username already exists'}), 400
    users[username] = {'online': False}
    return jsonify({'message': 'User registered successfully'}), 200

# Login a user
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    if username not in users:
        return jsonify({'error': 'Username does not exist'}), 400
    users[username]['online'] = True
    return jsonify({'message': 'User logged in successfully'}), 200

# Logout a user
@app.route('/logout', methods=['POST'])
def logout():
    data = request.json
    username = data['username']
    if username not in users:
        return jsonify({'error': 'Username does not exist'}), 400
    users[username]['online'] = False
    return jsonify({'message': 'User logged out successfully'}), 200

# Send a message
@socketio.on('send_message')
def send_message(data):
    username = data['username']
    message = data['message']
    room = data['room']
    if room not in messages:
        messages[room] = []
    messages[room].append({'username': username, 'message': message})
    emit('receive_message', data, broadcast=True)

# Get message history
@app.route('/get_messages', methods=['POST'])
def get_messages():
    data = request.json
    room = data['room']
    if room not in messages:
        return jsonify({'messages': []}), 200
    return jsonify({'messages': messages[room]}), 200

# Get online users
@app.route('/get_online_users', methods=['POST'])
def get_online_users():
    data = request.json
    room = data['room']
    online_users = [username for username, user in users.items() if user['online']]
    return jsonify({'online_users': online_users}), 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5003)