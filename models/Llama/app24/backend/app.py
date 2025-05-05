# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Database (for demonstration purposes)
users = []
profiles = []
connections = []
job_postings = []
messages = []
endorsements = []
achievements = []

# 4. Utility Functions
def get_user_by_id(user_id):
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_profile_by_user_id(user_id):
    for profile in profiles:
        if profile['user_id'] == user_id:
            return profile
    return None

# 5. API Routes
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    new_user = {
        'id': len(users) + 1,
        'username': data['username'],
        'email': data['email'],
        'password': data['password']
    }
    users.append(new_user)
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/profile', methods=['POST'])
def create_profile():
    data = request.json
    user = get_user_by_id(data['user_id'])
    if user:
        new_profile = {
            'id': len(profiles) + 1,
            'user_id': data['user_id'],
            'name': data['name'],
            'headline': data['headline'],
            'bio': data['bio']
        }
        profiles.append(new_profile)
        return jsonify({'message': 'Profile created successfully'}), 201
    return jsonify({'message': 'User not found'}), 404

@app.route('/api/connections', methods=['POST'])
def create_connection():
    data = request.json
    user1 = get_user_by_id(data['user1_id'])
    user2 = get_user_by_id(data['user2_id'])
    if user1 and user2:
        new_connection = {
            'id': len(connections) + 1,
            'user1_id': data['user1_id'],
            'user2_id': data['user2_id']
        }
        connections.append(new_connection)
        return jsonify({'message': 'Connection created successfully'}), 201
    return jsonify({'message': 'One or both users not found'}), 404

@app.route('/api/job_postings', methods=['POST'])
def create_job_posting():
    data = request.json
    user = get_user_by_id(data['user_id'])
    if user:
        new_job_posting = {
            'id': len(job_postings) + 1,
            'user_id': data['user_id'],
            'title': data['title'],
            'description': data['description']
        }
        job_postings.append(new_job_posting)
        return jsonify({'message': 'Job posting created successfully'}), 201
    return jsonify({'message': 'User not found'}), 404

@app.route('/api/messages', methods=['POST'])
def send_message():
    data = request.json
    sender = get_user_by_id(data['sender_id'])
    receiver = get_user_by_id(data['receiver_id'])
    if sender and receiver:
        new_message = {
            'id': len(messages) + 1,
            'sender_id': data['sender_id'],
            'receiver_id': data['receiver_id'],
            'content': data['content']
        }
        messages.append(new_message)
        return jsonify({'message': 'Message sent successfully'}), 201
    return jsonify({'message': 'One or both users not found'}), 404

@app.route('/api/endorsements', methods=['POST'])
def create_endorsement():
    data = request.json
    endorser = get_user_by_id(data['endorser_id'])
    endorsee = get_user_by_id(data['endorsee_id'])
    if endorser and endorsee:
        new_endorsement = {
            'id': len(endorsements) + 1,
            'endorser_id': data['endorser_id'],
            'endorsee_id': data['endorsee_id'],
            'skill': data['skill']
        }
        endorsements.append(new_endorsement)
        return jsonify({'message': 'Endorsement created successfully'}), 201
    return jsonify({'message': 'One or both users not found'}), 404

@app.route('/api/achievements', methods=['POST'])
def create_achievement():
    data = request.json
    user = get_user_by_id(data['user_id'])
    if user:
        new_achievement = {
            'id': len(achievements) + 1,
            'user_id': data['user_id'],
            'title': data['title'],
            'description': data['description']
        }
        achievements.append(new_achievement)
        return jsonify({'message': 'Achievement created successfully'}), 201
    return jsonify({'message': 'User not found'}), 404

# 6. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Route not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5047')))
