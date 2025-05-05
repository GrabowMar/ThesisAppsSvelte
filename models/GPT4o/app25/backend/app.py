from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory database for simplicity
user_data = {
    "mood": [],
    "stress": [],
    "journal": []
}

# Root endpoint to test app health
@app.route('/', methods=["GET"])
def home():
    return jsonify({"message": "Mental Health Tracking System Backend is running!"})

# Save mood input
@app.route('/api/mood', methods=["POST"])
def log_mood():
    mood = request.json.get("mood")
    date = request.json.get("date")
    if mood and date:
        user_data["mood"].append({"mood": mood, "date": date})
        return jsonify({"message": "Mood logged successfully!"}), 200
    return jsonify({"error": "Invalid input"}), 400

# Save stress input
@app.route('/api/stress', methods=["POST"])
def log_stress():
    stress = request.json.get("stress")
    date = request.json.get("date")
    if stress and date:
        user_data["stress"].append({"stress": stress, "date": date})
        return jsonify({"message": "Stress level logged successfully!"}), 200
    return jsonify({"error": "Invalid input"}), 400

# Save journaling entry
@app.route('/api/journal', methods=["POST"])
def save_journal():
    entry = request.json.get("entry")
    date = request.json.get("date")
    if entry and date:
        user_data["journal"].append({"entry": entry, "date": date})
        return jsonify({"message": "Journal entry saved!"}), 200
    return jsonify({"error": "Invalid input"}), 400

# Fetch logged data
@app.route('/api/data', methods=["GET"])
def fetch_data():
    return jsonify(user_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5289')), debug=True)
