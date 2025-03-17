# app.py
from flask import Flask, jsonify, request
import json

app = Flask(__name__)

# In-memory data store (replace with a database for production)
workouts = []
exercises = [
    {"id": 1, "name": "Bench Press", "description": "Chest exercise"},
    {"id": 2, "name": "Pull-ups", "description": "Back exercise"},
    {"id": 3, "name": "Squats", "description": "Legs exercise"},
]

# API endpoint to get all exercises
@app.route("/exercises", methods=["GET"])
def get_exercises():
    return jsonify(exercises)

# API endpoint to get all workouts
@app.route("/workouts", methods=["GET"])
def get_workouts():
    return jsonify(workouts)

# API endpoint to add a new workout
@app.route("/workouts", methods=["POST"])
def add_workout():
    data = request.json
    workouts.append(data)
    return jsonify(data), 201

# API endpoint to get workout statistics
@app.route("/workouts/stats", methods=["GET"])
def get_workout_stats():
    stats = {}
    for workout in workouts:
        exercise_id = workout["exercise_id"]
        if exercise_id not in stats:
            stats[exercise_id] = {"total_reps": 0, "total_weight": 0}
        stats[exercise_id]["total_reps"] += workout["reps"]
        stats[exercise_id]["total_weight"] += workout["weight"]
    return jsonify(stats)

if __name__ == "__main__":
    app.run(port=5033)
