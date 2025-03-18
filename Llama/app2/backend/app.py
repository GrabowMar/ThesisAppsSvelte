from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, join_room, leave_room, send
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"  # Change this for production
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage (Replace with a database for production)
users = {}
rooms = {"general": {"messages": []}}  # Default room

@app.route("/")
def home():
    """
    Render the base template or respond with a message.
    """
    return jsonify({"status": "success", "message": "Welcome to the chat backend!"})

# === User management ===
@app.route("/register", methods=["POST"])
def register():
    """
    Register new users with username and password.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username in users:
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users[username] = {"password": hashed_password, "rooms": ["general"]}
    return jsonify({"status": "success", "message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    """
    Authenticate users with username and password.
    """
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    user = users.get(username)
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"status": "success", "message": "Login successful", "user": username}), 200


# === Chat and Rooms ===
@app.route("/rooms", methods=["GET"])
def get_rooms():
    """
    Get a list of all chat rooms.
    """
    return jsonify({"rooms": list(rooms.keys())})


@app.route("/rooms", methods=["POST"])
def create_room():
    """
    Create a new chat room.
    """
    data = request.get_json()
    room_name = data.get("room_name")

    if room_name in rooms:
        return jsonify({"error": "Room already exists"}), 400

    rooms[room_name] = {"messages": []}
    return jsonify({"status": "success", "message": f"Room '{room_name}' created successfully"}), 201


@socketio.on("join")
def handle_join(data):
    """
    Handle users joining a chat room.
    """
    username = data.get("username")
    room = data.get("room")

    if not username or not room:
        return send("Invalid join request", to=request.sid)

    join_room(room)
    send(f"{username} has joined the room.", to=room)


@socketio.on("leave")
def handle_leave(data):
    """
    Handle users leaving a chat room.
    """
    username = data.get("username")
    room = data.get("room")

    if not username or not room:
        return send("Invalid leave request", to=request.sid)

    leave_room(room)
    send(f"{username} has left the room.", to=room)


@socketio.on("message")
def handle_message(data):
    """
    Handle sending messages in a room.
    """
    username = data.get("username")
    room = data.get("room")
    message = data.get("message")

    if not username or not room or not message:
        return send("Invalid message", to=request.sid)

    message_data = {"username": username, "message": message}
    rooms[room]["messages"].append(message_data)
    send(message_data, to=room, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5003)
