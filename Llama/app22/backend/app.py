# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (simple in-memory storage for demonstration purposes)
# In a real application, you'd use a proper database like MySQL or PostgreSQL
vocabulary = [
    {"id": 1, "word": "hello", "translation": "bonjour", "language": "French"},
    {"id": 2, "word": "goodbye", "translation": "au revoir", "language": "French"},
    {"id": 3, "word": "thank you", "translation": "merci", "language": "French"},
]

grammar_exercises = [
    {"id": 1, "question": "What is the correct verb form?", "options": ["Option 1", "Option 2", "Option 3"], "correct": 1, "language": "French"},
    {"id": 2, "question": "What is the correct sentence structure?", "options": ["Option 1", "Option 2", "Option 3"], "correct": 2, "language": "French"},
]

progress = {}

# 4. Authentication Logic (simple token-based authentication for demonstration purposes)
# In a real application, you'd use a proper authentication library like Flask-Login or Flask-Security
users = {"user1": "password1"}
tokens = {}

# 5. Utility Functions
def authenticate_user(username, password):
    if username in users and users[username] == password:
        token = os.urandom(16).hex()
        tokens[token] = username
        return token
    return None

def validate_token(token):
    return token in tokens

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    token = authenticate_user(username, password)
    if token:
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/vocabulary', methods=['GET'])
def get_vocabulary():
    return jsonify(vocabulary)

@app.route('/api/grammar-exercises', methods=['GET'])
def get_grammar_exercises():
    return jsonify(grammar_exercises)

@app.route('/api/progress', methods=['GET', 'POST'])
def track_progress():
    token = request.headers.get('Authorization')
    if not validate_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    if request.method == 'GET':
        username = tokens[token]
        return jsonify(progress.get(username, {}))
    elif request.method == 'POST':
        data = request.get_json()
        username = tokens[token]
        progress[username] = data
        return jsonify({'message': 'Progress updated'})

@app.route('/api/quiz', methods=['POST'])
def submit_quiz():
    token = request.headers.get('Authorization')
    if not validate_token(token):
        return jsonify({'error': 'Invalid token'}), 401
    data = request.get_json()
    # Evaluate quiz answers
    score = 0
    for answer in data['answers']:
        # Simplified evaluation for demonstration purposes
        if answer['correct']:
            score += 1
    return jsonify({'score': score})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5043)
