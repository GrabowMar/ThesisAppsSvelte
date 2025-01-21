from flask import Flask, request
from flask_socketio import SocketIO, join_room, leave_room, send
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}

@app.route('/')
def index():
    return "Chat server is running!"

@socketio.on('join')
def handle_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    users[request.sid] = {'username': username, 'room': room}
    send(f"{username} has joined the room.", to=room)

@socketio.on('message')
def handle_message(data):
    room = users[request.sid]['room']
    username = users[request.sid]['username']
    message = data['message']
    send({'username': username, 'message': message}, to=room)

@socketio.on('leave')
def handle_leave(data):
    room = users[request.sid]['room']
    username = users[request.sid]['username']
    leave_room(room)
    send(f"{username} has left the room.", to=room)
    users.pop(request.sid, None)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        room = users[request.sid]['room']
        username = users[request.sid]['username']
        send(f"{username} has disconnected.", to=room)
        users.pop(request.sid, None)

if __name__ == '__main__':
    try:
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5003,
                    allow_unsafe_werkzeug=True)  #added allow_unsafe_werkzeug=True
    except Exception as e:
        print(f"Failed to start server: {e}")
