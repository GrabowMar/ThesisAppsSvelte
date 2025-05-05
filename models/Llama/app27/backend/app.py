# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (Simple in-memory data store for demonstration)
# In a real application, consider using a database like SQLite or PostgreSQL
players = [
    {"id": 1, "name": "John Doe", "position": "Forward"},
    {"id": 2, "name": "Jane Smith", "position": "Midfielder"},
]

performances = [
    {"id": 1, "player_id": 1, "match_id": 1, "goals": 2, "assists": 1},
    {"id": 2, "player_id": 2, "match_id": 1, "goals": 0, "assists": 2},
]

training_schedules = [
    {"id": 1, "date": "2024-03-01", "activity": "Sprinting"},
    {"id": 2, "date": "2024-03-02", "activity": "Strength Training"},
]

matches = [
    {"id": 1, "date": "2024-03-15", "opponent": "Team X"},
    {"id": 2, "date": "2024-03-22", "opponent": "Team Y"},
]

injuries = [
    {"id": 1, "player_id": 1, "injury": "Knee sprain", "recovery_date": "2024-03-10"},
]

# 4. Authentication Logic (Simplified, not recommended for production without proper security measures)
# For demonstration purposes only

# 5. Utility Functions
def get_player_by_id(player_id):
    for player in players:
        if player["id"] == player_id:
            return player
    return None

# 6. API Routes
@app.route('/api/players', methods=['GET'])
def get_players():
    return jsonify(players)

@app.route('/api/players', methods=['POST'])
def create_player():
    new_player = {
        "id": len(players) + 1,
        "name": request.json['name'],
        "position": request.json['position']
    }
    players.append(new_player)
    return jsonify(new_player), 201

@app.route('/api/performances', methods=['GET'])
def get_performances():
    return jsonify(performances)

@app.route('/api/training-schedules', methods=['GET'])
def get_training_schedules():
    return jsonify(training_schedules)

@app.route('/api/matches', methods=['GET'])
def get_matches():
    return jsonify(matches)

@app.route('/api/injuries', methods=['GET'])
def get_injuries():
    injuries_with_player_name = []
    for injury in injuries:
        player = get_player_by_id(injury["player_id"])
        if player:
            injury_with_name = injury.copy()
            injury_with_name["player_name"] = player["name"]
            injuries_with_player_name.append(injury_with_name)
    return jsonify(injuries_with_player_name)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5053')))
