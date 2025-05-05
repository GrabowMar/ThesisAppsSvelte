from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Mock data for simplicity
players = [
    {"id": 1, "name": "John Doe", "position": "Forward", "injuries": [], "stats": {"games": 5, "goals": 10}},
    {"id": 2, "name": "Jane Smith", "position": "Defender", "injuries": [{"date": "2023-09-01", "injury": "ankle strain"}], "stats": {"games": 5, "goals": 0}},
]

schedule = [
    {"id": 1, "date": "2023-10-15", "opponent": "Team A", "type": "Training"},
    {"id": 2, "date": "2023-10-22", "opponent": "Team B", "type": "Match"},
]

@app.route('/api/players', methods=['GET'])
def get_players():
    return jsonify(players)

@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.get_json()
    new_player = {
        "id": len(players) + 1,
        "name": data["name"],
        "position": data["position"],
        "injuries": [],
        "stats": {"games": 0, "goals": 0}
    }
    players.append(new_player)
    return jsonify(new_player), 201

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    return jsonify(schedule)

@app.route('/api/schedule', methods=['POST'])
def add_schedule():
    data = request.get_json()
    new_event = {
        "id": len(schedule) + 1,
        "date": data["date"],
        "opponent": data["opponent"],
        "type": data["type"],
    }
    schedule.append(new_event)
    return jsonify(new_event), 201

@app.route('/api/statistics', methods=['POST'])
def update_statistics():
    data = request.get_json()
    player_id = data["id"]
    player = next((p for p in players if p['id'] == player_id), None)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    if "games" in data:
        player["stats"]["games"] += data["games"]
    if "goals" in data:
        player["stats"]["goals"] += data["goals"]
    return jsonify(player), 200

@app.route('/api/injuries/<int:id>', methods=['POST'])
def add_injury(id):
    data = request.get_json()
    player = next((p for p in players if p['id'] == id), None)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    player["injuries"].append(data)
    return jsonify(player), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5293)
