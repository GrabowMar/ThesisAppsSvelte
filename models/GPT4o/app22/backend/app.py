from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# In-memory database simulation
users = {}
progress = {}

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    username = data.get('username')
    if username in users:
        return jsonify({"error": "User already exists!"}), 400
    users[username] = {"password": data.get('password'), "language": data.get('language')}
    progress[username] = {"vocabulary": [], "grammar": {}, "quiz_scores": []}
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """User Login"""
    data = request.json
    username = data.get('username')
    if username not in users or users[username]["password"] != data.get('password'):
        return jsonify({"error": "Invalid credentials!"}), 401
    return jsonify({"message": "Login successful!"}), 200

@app.route('/api/progress/<username>', methods=['GET'])
def get_progress(username):
    """Fetch user progress"""
    if username not in progress:
        return jsonify({"error": "User not found!"}), 404
    return jsonify(progress[username]), 200

@app.route('/api/vocabulary', methods=['POST'])
def add_vocabulary():
    """Add vocabulary words to user progress"""
    data = request.json
    username = data.get('username')
    if username not in progress:
        return jsonify({"error": "User not found!"}), 404
    new_words = data.get('words', [])
    progress[username]["vocabulary"].extend(new_words)
    return jsonify({"message": "Vocabulary updated!"}), 200

@app.route('/api/quiz', methods=['POST'])
def submit_quiz():
    """Submit a quiz score"""
    data = request.json
    username = data.get('username')
    if username not in progress:
        return jsonify({"error": "User not found!"}), 404
    score = data.get('score', 0)
    progress[username]["quiz_scores"].append(score)
    return jsonify({"message": "Quiz submitted successfully!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5283)
