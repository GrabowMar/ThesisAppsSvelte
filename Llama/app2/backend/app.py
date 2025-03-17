from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# In-memory storage for chat messages and online status
chat_messages = []
online_users = {}

# Backend route for login
@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    online_users[username] = True
    return jsonify({'message': 'Logged in successfully'}), 200

# Backend route for register
@app.route('/register', methods=['POST'])
def register():
    username = request.json['username']
    # Validate if username is not already taken
    if username not in online_users:
        online_users[username] = False
        return jsonify({'message': 'Registered successfully'}), 200
    else:
        return jsonify({'message': 'Username already taken'}), 400

# Backend route for dashboard
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return jsonify({'message': 'Welcome to the dashboard'}), 200

# SocketIO event for sending messages
@socketio.on('send_message')
def send_message(data):
    chat_messages.append({'username': data['username'], 'message': data['message'], 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    emit('receive_message', {'username': data['username'], 'message': data['message'], 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}, broadcast=True)

# SocketIO event for updating online status
@socketio.on('update_online_status')
def update_online_status(data):
    online_users[data['username']] = data['status']
    emit('update_online_status', {'username': data['username'], 'status': data['status']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5003)
