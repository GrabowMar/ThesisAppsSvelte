# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    online_status = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(80), unique=True, nullable=False)

# 4. Authentication Logic (if needed)
class Authentication:
    def __init__(self):
        self.users = {}

    def login(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            user.online_status = True
            db.session.commit()
            return jsonify({'message': 'Logged in successfully'}), 200
        else:
            return jsonify({'message': 'Invalid username'}), 401

    def logout(self, username):
        user = User.query.filter_by(username=username).first()
        if user:
            user.online_status = False
            db.session.commit()
            return jsonify({'message': 'Logged out successfully'}), 200
        else:
            return jsonify({'message': 'Invalid username'}), 401

# 5. Utility Functions
def get_user_id(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return user.id
    else:
        return None

def get_chat_room_id(room_name):
    room = ChatRoom.query.filter_by(room_name=room_name).first()
    if room:
        return room.id
    else:
        return None

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    authentication = Authentication()
    username = request.json['username']
    return authentication.login(username)

@app.route('/api/logout', methods=['POST'])
def logout():
    authentication = Authentication()
    username = request.json['username']
    return authentication.logout(username)

@app.route('/api/send_message', methods=['POST'])
def send_message():
    sender_username = request.json['sender_username']
    receiver_username = request.json['receiver_username']
    message = request.json['message']
    sender_id = get_user_id(sender_username)
    receiver_id = get_user_id(receiver_username)
    if sender_id and receiver_id:
        new_message = Message(sender_id=sender_id, receiver_id=receiver_id, message=message)
        db.session.add(new_message)
        db.session.commit()
        return jsonify({'message': 'Message sent successfully'}), 200
    else:
        return jsonify({'message': 'Invalid sender or receiver'}), 401

@app.route('/api/get_messages', methods=['POST'])
def get_messages():
    sender_username = request.json['sender_username']
    receiver_username = request.json['receiver_username']
    sender_id = get_user_id(sender_username)
    receiver_id = get_user_id(receiver_username)
    if sender_id and receiver_id:
        messages = Message.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).all()
        message_list = []
        for message in messages:
            message_list.append({'sender_username': sender_username, 'receiver_username': receiver_username, 'message': message.message})
        return jsonify(message_list), 200
    else:
        return jsonify({'message': 'Invalid sender or receiver'}), 401

@app.route('/api/create_chat_room', methods=['POST'])
def create_chat_room():
    room_name = request.json['room_name']
    new_room = ChatRoom(room_name=room_name)
    db.session.add(new_room)
    db.session.commit()
    return jsonify({'message': 'Chat room created successfully'}), 200

@app.route('/api/get_chat_rooms', methods=['GET'])
def get_chat_rooms():
    rooms = ChatRoom.query.all()
    room_list = []
    for room in rooms:
        room_list.append({'room_name': room.room_name})
    return jsonify(room_list), 200

# 7. Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'message': 'Page not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5003')))
