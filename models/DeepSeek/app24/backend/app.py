from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os
from functools import wraps
import json
from datetime import datetime

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)

# In-memory database (replace with a real database in production)
users = {}
profiles = {}
connections = {}
jobs = {}
messages = {}
endorsements = {}

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Utility Functions
def generate_id():
    return str(uuid.uuid4())

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400
    
    if data['email'] in users:
        return jsonify({"error": "User already exists"}), 409
    
    user_id = generate_id()
    users[data['email']] = {
        'id': user_id,
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'name': data.get('name', '')
    }
    
    # Initialize profile
    profiles[user_id] = {
        'user_id': user_id,
        'headline': '',
        'summary': '',
        'experience': [],
        'education': [],
        'skills': []
    }
    
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password required"}), 400
    
    user = users.get(data['email'])
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    session['user_id'] = user['id']
    return jsonify({"message": "Login successful"}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"}), 200

# Profile Routes
@app.route('/api/profile', methods=['GET'])
@login_required
def get_profile():
    user_id = session['user_id']
    profile = profiles.get(user_id, {})
    user_data = next((u for u in users.values() if u['id'] == user_id), {})
    return jsonify({
        **profile,
        'name': user_data.get('name', ''),
        'email': user_data.get('email', '')
    }), 200

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    user_id = session['user_id']
    data = request.json
    
    profiles[user_id] = {
        'user_id': user_id,
        'headline': data.get('headline', ''),
        'summary': data.get('summary', ''),
        'experience': data.get('experience', []),
        'education': data.get('education', []),
        'skills': data.get('skills', [])
    }
    
    # Update name if provided
    if 'name' in data:
        for email, user in users.items():
            if user['id'] == user_id:
                users[email]['name'] = data['name']
                break
    
    return jsonify({"message": "Profile updated successfully"}), 200

# Connection Routes
@app.route('/api/connections', methods=['GET'])
@login_required
def get_connections():
    user_id = session['user_id']
    user_connections = connections.get(user_id, [])
    connection_details = []
    
    for conn_id in user_connections:
        profile = profiles.get(conn_id, {})
        user = next((u for u in users.values() if u['id'] == conn_id), {})
        
        if profile and user:
            connection_details.append({
                'id': conn_id,
                'name': user.get('name', ''),
                'headline': profile.get('headline', '')
            })
    
    return jsonify(connection_details), 200

@app.route('/api/connections/<target_id>', methods=['POST'])
@login_required
def connect(target_id):
    user_id = session['user_id']
    
    if user_id not in connections:
        connections[user_id] = []
    
    if target_id not in connections[user_id]:
        connections[user_id].append(target_id)
    
    # Add reciprocal connection (symmetric relationship)
    if target_id not in connections:
        connections[target_id] = []
    
    if user_id not in connections[target_id]:
        connections[target_id].append(user_id)
    
    return jsonify({"message": "Connection established"}), 201

# Job Routes
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    return jsonify(list(jobs.values())), 200

@app.route('/api/jobs', methods=['POST'])
@login_required
def post_job():
    user_id = session['user_id']
    job_id = generate_id()
    data = request.json
    
    jobs[job_id] = {
        'id': job_id,
        'title': data['title'],
        'description': data['description'],
        'company': data.get('company', ''),
        'location': data.get('location', 'Remote'),
        'posted_by': user_id,
        'created_at': datetime.now().isoformat(),
        'applicants': []
    }
    
    return jsonify(jobs[job_id]), 201

@app.route('/api/jobs/<job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    user_id = session['user_id']
    jobs[job_id]['applicants'].append(user_id)
    return jsonify({"message": "Application submitted"}), 200

# Endorsement Routes
@app.route('/api/endorsements/<user_id>', methods=['GET'])
def get_endorsements(user_id):
    user_endorsements = [e for e in endorsements.values() if e['target_id'] == user_id]
    return jsonify(user_endorsements), 200

@app.route('/api/endorsements', methods=['POST'])
@login_required
def endorse():
    user_id = session['user_id']
    data = request.json
    endorsement_id = generate_id()
    
    endorsements[endorsement_id] = {
        'id': endorsement_id,
        'skill': data['skill'],
        'message': data.get('message', ''),
        'endorser_id': user_id,
        'target_id': data['target_id'],
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify(endorsements[endorsement_id]), 201

# Messaging Routes
@app.route('/api/messages', methods=['GET'])
@login_required
def get_messages():
    user_id = session['user_id']
    user_messages = [m for m in messages.values() if m['receiver_id'] == user_id or m['sender_id'] == user_id]
    return jsonify(user_messages), 200

@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    user_id = session['user_id']
    data = request.json
    message_id = generate_id()
    
    messages[message_id] = {
        'id': message_id,
        'content': data['content'],
        'sender_id': user_id,
        'receiver_id': data['receiver_id'],
        'created_at': datetime.now().isoformat(),
        'read': False
    }
    
    return jsonify(messages[message_id]), 201

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5207')))
