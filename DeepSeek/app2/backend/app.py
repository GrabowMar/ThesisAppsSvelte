from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# In-memory data storage
users = {}  # {user_id: {name: str, online: bool}}
messages = []  # [{id: int, room: str, user_id: str, text: str, timestamp: str}]

# Helper functions
def generate_user_id():
    return f"user_{len(users) + 1}"

def generate_message_id():
    return len(messages) + 1

# Routes
@app.route("/register", methods=["POST"])
def register_user():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"error": "Name is required"}), 400
    user_id = generate_user_id()
    users[user_id] = {"name": name, "online": True}
    return jsonify({"user_id": user_id, "name": name}), 201

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json
    user_id = data.get("user_id")
    room = data.get("room")
    text = data.get("text")
    if not user_id or not text or not room:
        return jsonify({"error": "Missing required fields"}), 400
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    message = {
        "id": generate_message_id(),
        "room": room,
        "user_id": user_id,
        "text": text,
        "timestamp": datetime.now().isoformat(),
    }
    messages.append(message)
    return jsonify(message), 201

@app.route("/messages/<room>", methods=["GET"])
def get_messages(room):
    room_messages = [msg for msg in messages if msg["room"] == room]
    return jsonify(room_messages), 200

@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users), 200

@app.route("/logout", methods=["POST"])
def logout_user():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404
    users[user_id]["online"] = False
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5163, debug=True)
