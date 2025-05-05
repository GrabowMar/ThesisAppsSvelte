from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# In-memory data storage for demonstration
workouts = []
exercise_library = [
    {"id": 1, "name": "Push-ups", "category": "Bodyweight", "met": 3.8},
    {"id": 2, "name": "Running", "category": "Cardio", "met": 8.0},
    {"id": 3, "name": "Weight Lifting", "category": "Strength", "met": 6.0}
]

# Utility functions
def calculate_stats():
    total_workouts = len(workouts)
    total_duration = sum(w['duration'] for w in workouts)
    total_calories = sum(w['calories'] for w in workouts)
    
    return {
        "total_workouts": total_workouts,
        "total_duration": total_duration,
        "total_calories": total_calories,
        "avg_duration": total_duration // total_workouts if total_workouts else 0
    }

# API Routes
@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    return jsonify(exercise_library)

@app.route('/api/workouts', methods=['GET', 'POST'])
def handle_workouts():
    if request.method == 'POST':
        try:
            data = request.get_json()
            workout = {
                "id": len(workouts) + 1,
                "exercise_id": data['exercise_id'],
                "duration": float(data['duration']),
                "date": datetime.now().isoformat(),
                "calories": float(data['calories'])
            }
            workouts.append(workout)
            return jsonify(workout), 201
        except KeyError:
            abort(400, description="Invalid workout data")
    
    return jsonify(workouts)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(calculate_stats())

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": error.description}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5593')))
