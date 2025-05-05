from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize the Flask application
app = Flask(__name__)
CORS(app)

# In-Memory Database Mockup (Replace with actual DB in production)
users = {}  # {username: {password, workouts: {date: [exercises]}}}

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "All fields are required!"}), 400

    if username in users:
        return jsonify({"error": "Username already exists!"}), 409

    users[username] = {"password": password, "workouts": {}}
    return jsonify({"message": "User registered successfully!"}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.get(username)
    if not user or user['password'] != password:
        return jsonify({"error": "Invalid credentials!"}), 401

    return jsonify({"message": "Login successful!", "username": username}), 200


@app.route('/api/log_workout', methods=['POST'])
def log_workout():
    data = request.json
    username = data.get('username')
    date = data.get('date')
    exercises = data.get('exercises')

    if not username or not date or not exercises:
        return jsonify({"error": "All fields are required!"}), 400

    user = users.get(username)
    if not user:
        return jsonify({"error": "User not found!"}), 404

    if date not in user['workouts']:
        user['workouts'][date] = []

    user['workouts'][date].extend(exercises)

    return jsonify({"message": "Workout logged successfully!"}), 201


@app.route('/api/progress', methods=['GET'])
def progress():
    username = request.args.get('username')

    user = users.get(username)
    if not user:
        return jsonify({"error": "User not found!"}), 404

    return jsonify({"workouts": user['workouts']}), 200


@app.route('/api/exercise_library', methods=['GET'])
def exercise_library():
    exercises = [
        "Push-Ups",
        "Sit-Ups",
        "Squats",
        "Pull-Ups",
        "Deadlifts",
        "Bench Press",
        "Running",
        "Yoga"
    ]
    return jsonify({"exercises": exercises}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5273')))
