# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Data Storage (Replace with a database in a real application)
workouts = []
exercises = [
    {"id": 1, "name": "Bench Press", "type": "Strength"},
    {"id": 2, "name": "Squats", "type": "Strength"},
    {"id": 3, "name": "Deadlifts", "type": "Strength"},
    {"id": 4, "name": "Running", "type": "Cardio"},
    {"id": 5, "name": "Swimming", "type": "Cardio"}
]

# 4. Authentication Logic (Placeholder - implement actual authentication later)
# For simplicity, we're skipping authentication in this example

# 5. Utility Functions
def calculate_statistics():
    """Calculates basic workout statistics."""
    total_workouts = len(workouts)
    if total_workouts == 0:
        return {"total_workouts": 0}

    workout_types = {}
    for workout in workouts:
        for exercise in workout["exercises"]:
            exercise_name = exercise["name"]
            if exercise_name in workout_types:
                workout_types[exercise_name] +=1
            else:
                workout_types[exercise_name] = 1


    return {
        "total_workouts": total_workouts,
        "most_frequent_exercises": workout_types,
        "average_duration": 0  # Placeholder - implement later if tracking workout duration
    }


# 6. API Routes
@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    """Returns the list of available exercises."""
    return jsonify(exercises)


@app.route('/api/workouts', methods=['GET', 'POST'])
def handle_workouts():
    """Handles workout creation and retrieval."""
    if request.method == 'GET':
        return jsonify(workouts)
    elif request.method == 'POST':
        data = request.get_json()
        if not data or "exercises" not in data:
            return jsonify({"error": "Invalid workout data"}), 400

        # Validate workout data (e.g., check if exercises exist)
        for exercise in data["exercises"]:
            exercise_exists = any(ex["name"] == exercise["name"] for ex in exercises)
            if not exercise_exists:
                return jsonify({"error": f"Exercise '{exercise['name']}' does not exist"}), 400

        workout = {
            "id": len(workouts) + 1,
            "date": datetime.now().isoformat(),  # Add timestamp
            "exercises": data["exercises"]
        }
        workouts.append(workout)
        return jsonify(workout), 201  # 201 Created


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Returns workout statistics."""
    stats = calculate_statistics()
    return jsonify(stats)


# 7. Error Handlers (Example)
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5433')), debug=True)
