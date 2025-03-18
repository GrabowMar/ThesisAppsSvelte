from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity
users = []
exercises = []
workouts = []

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    for user in users:
        if user['username'] == username:
            return jsonify({"error": "Username already exists"}), 400

    users.append({"username": username, "password": password})
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    for user in users:
        if user['username'] == username and user['password'] == password:
            return jsonify({"message": "Login successful"}), 200

    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/exercises', methods=['GET'])
def get_exercises():
    return jsonify(exercises), 200

@app.route('/exercises', methods=['POST'])
def add_exercise():
    data = request.get_json()
    exercise = {
        "id": len(exercises) + 1,
        "name": data.get('name'),
        "description": data.get('description')
    }
    exercises.append(exercise)
    return jsonify(exercise), 201

@app.route('/workouts', methods=['POST'])
def log_workout():
    data = request.get_json()
    workout = {
        "id": len(workouts) + 1,
        "username": data.get('username'),
        "exercise_id": data.get('exercise_id'),
        "date": datetime.now().strftime('%Y-%m-%d'),
        "details": data.get('details')
    }
    workouts.append(workout)
    return jsonify(workout), 201

@app.route('/workouts/<username>', methods=['GET'])
def get_workouts(username):
    user_workouts = [workout for workout in workouts if workout['username'] == username]
    return jsonify(user_workouts), 200

@app.route('/statistics/<username>', methods=['GET'])
def get_statistics(username):
    user_workouts = [workout for workout in workouts if workout['username'] == username]
    total_workouts = len(user_workouts)
    exercise_counts = {}

    for workout in user_workouts:
        exercise_id = workout['exercise_id']
        if exercise_id in exercise_counts:
            exercise_counts[exercise_id] += 1
        else:
            exercise_counts[exercise_id] = 1

    statistics = {
        "total_workouts": total_workouts,
        "exercise_counts": exercise_counts
    }
    return jsonify(statistics), 200

if __name__ == '__main__':
    app.run(port=5113)
