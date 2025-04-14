# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# In-memory data store for demonstration purposes
data_store = {
    "mood": [],
    "stress": [],
    "journal": [],
    "coping_strategies": [
        "Meditation",
        "Deep Breathing",
        "Physical Exercise",
        "Journaling",
        "Seeking Social Support"
    ],
    "reminders": []
}

# API Routes
@app.route('/api/mood', methods=['POST'])
def track_mood():
    mood_data = request.json
    data_store['mood'].append(mood_data)
    return jsonify({"message": "Mood tracked successfully"}), 201

@app.route('/api/stress', methods=['POST'])
def track_stress():
    stress_data = request.json
    data_store['stress'].append(stress_data)
    return jsonify({"message": "Stress level tracked successfully"}), 201

@app.route('/api/journal', methods=['POST'])
def add_journal_entry():
    journal_entry = request.json
    data_store['journal'].append(journal_entry)
    return jsonify({"message": "Journal entry added successfully"}), 201

@app.route('/api/coping_strategies', methods=['GET'])
def get_coping_strategies():
    return jsonify(data_store['coping_strategies'])

@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    reminder = request.json
    data_store['reminders'].append(reminder)
    return jsonify({"message": "Reminder added successfully"}), 201

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    return jsonify(data_store['reminders'])

@app.route('/api/progress', methods=['GET'])
def get_progress():
    # Simplified progress data for demonstration
    progress_data = {
        "mood": len(data_store['mood']),
        "stress": len(data_store['stress']),
        "journal_entries": len(data_store['journal'])
    }
    return jsonify(progress_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5049')))
