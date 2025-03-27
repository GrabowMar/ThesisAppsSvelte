# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity (replace with a database in production)
workouts = []
exercise_library = [
    {"id": 1, "name": "Push-ups", "muscle_group": "Chest"},
    {"id": 2, "name": "Squats", "muscle_group": "Legs"},
    {"id": 3, "name": "Pull-ups", "muscle_group": "Back"},
]

# 5. Utility Functions
def calculate_statistics(workouts):
    total_workouts = len(workouts)
    total_duration = sum(workout.get("duration", 0) for workout in workouts)
    total_calories = sum(workout.get("calories_burned", 0) for workout in workouts)
    return {
        "total_workouts": total_workouts,
        "total_duration": total_duration,
        "total_calories": total_calories,
    }

# 6. API Routes
@app.route("/api/workouts", methods=["GET"])
def get_workouts():
    return jsonify(workouts)

@app.route("/api/workouts", methods=["POST"])
def add_workout():
    data = request.json
    data["id"] = len(workouts) + 1
    data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workouts.append(data)
    return jsonify({"message": "Workout added successfully", "workout": data}), 201

@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    stats = calculate_statistics(workouts)
    return jsonify(stats)

@app.route("/api/exercises", methods=["GET"])
def get_exercises():
    return jsonify(exercise_library)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5193")))
