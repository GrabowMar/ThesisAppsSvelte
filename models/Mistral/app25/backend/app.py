# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# Simulated database
users = []
mood_logs = []
stress_logs = []
journal_entries = []

# 4. Authentication Logic (if needed)
# 5. Utility Functions
def find_user(username):
    return next((user for user in users if user['username'] == username), None)

# 6. API Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    if find_user(username):
        return jsonify({'message': 'User already exists'}), 400
    users.append(data)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = find_user(data.get('username'))
    if not user or user['password'] != data.get('password'):
        return jsonify({'message': 'Invalid credentials'}), 401
    return jsonify({'message': 'Login successful'}), 200

@app.route('/log_mood', methods=['POST'])
def log_mood():
    data = request.json
    mood_logs.append(data)
    return jsonify({'message': 'Mood logged successfully'}), 201

@app.route('/log_stress', methods=['POST'])
def log_stress():
    data = request.json
    stress_logs.append(data)
    return jsonify({'message': 'Stress logged successfully'}), 201

@app.route('/journal', methods=['POST'])
def journal():
    data = request.json
    data['timestamp'] = datetime.now().isoformat()
    journal_entries.append(data)
    return jsonify({'message': 'Journal entry logged successfully'}), 201

@app.route('/coping_strategies', methods=['GET'])
def coping_strategies():
    # Simulated coping strategies
    strategies = [
        "Take a deep breath",
        "Go for a walk",
        "Talk to a friend",
        "Practice mindfulness"
    ]
    return jsonify(strategies), 200

@app.route('/progress', methods=['GET'])
def progress():
    # Simulated progress data
    progress_data = {
        "mood_logs": mood_logs,
        "stress_logs": stress_logs,
        "journal_entries": journal_entries
    }
    return jsonify(progress_data), 200

@app.route('/reminders', methods=['GET'])
def reminders():
    # Simulated reminders
    reminders_data = [
        "Drink water",
        "Take a short break",
        "Stretch your body"
    ]
    return jsonify(reminders_data), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5129')))
