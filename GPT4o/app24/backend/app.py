from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Mock storage for demonstration (simulate database)
users = []
connections = []
job_posts = []
messages = []
skills_endorsements = []

# ---- API ROUTES ----

# User Registration
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if any(user['email'] == data['email'] for user in users):
        return jsonify({"error": "Email already registered"}), 400
    users.append(data)
    return jsonify({"message": "User registered successfully"}), 201

# User Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = next((user for user in users if user['email'] == data['email'] and user['password'] == data['password']), None)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    return jsonify({"message": "Login successful", "user": user}), 200

# Job Posting
@app.route('/api/jobs', methods=['POST'])
def post_job():
    data = request.json
    job_posts.append(data)
    return jsonify({"message": "Job posted successfully"}), 201

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    return jsonify(job_posts), 200

# Connection Management
@app.route('/api/connections', methods=['POST'])
def add_connection():
    data = request.json
    connections.append(data)
    return jsonify({"message": "Connection added"}), 201

@app.route('/api/connections', methods=['GET'])
def get_connections():
    return jsonify(connections), 200

# Messaging
@app.route('/api/messages', methods=['POST'])
def send_message():
    data = request.json
    messages.append(data)
    return jsonify({"message": "Message sent"}), 201

@app.route('/api/messages', methods=['GET'])
def get_messages():
    return jsonify(messages), 200

# Skill Endorsement
@app.route('/api/skills', methods=['POST'])
def endorse_skill():
    data = request.json
    skills_endorsements.append(data)
    return jsonify({"message": "Skill endorsed successfully"}), 201

@app.route('/api/skills', methods=['GET'])
def get_skills():
    return jsonify(skills_endorsements), 200

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5287')))
