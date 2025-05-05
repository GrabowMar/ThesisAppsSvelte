from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# App configuration
app = Flask(__name__)
CORS(app)

# Mock database for simplicity
users = {
    "sample_user": {
        "username": "sample_user",
        "carbon_footprint": 100,  # Example metric in kg CO2
        "challenges_completed": 2,
        "resource_consumption": {
            "water": 150,  # liters per day
            "electricity": 30  # kWh per month
        },
        "eco_tips": ["Switch to LED bulbs", "Use a reusable water bottle"],
        "community_rank": 5
    }
}

@app.route('/api/carbon-footprint', methods=['GET'])
def get_carbon_footprint():
    """Return the user's current carbon footprint."""
    username = request.args.get('username', 'sample_user')
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"carbon_footprint": user_data["carbon_footprint"]})

@app.route('/api/challenges', methods=['POST'])
def create_challenge():
    """Allow users to create a new sustainability challenge."""
    data = request.get_json()
    username = data.get('username')
    if username not in users:
        return jsonify({"error": "User not found"}), 404

    # Increment challenges and return success
    users[username]["challenges_completed"] += 1
    return jsonify({"message": "Challenge added successfully!", "challenges_completed": users[username]["challenges_completed"]})

@app.route('/api/resource-consumption', methods=['GET'])
def get_resource_consumption():
    """Return details of a user's resource consumption."""
    username = request.args.get('username', 'sample_user')
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user_data["resource_consumption"])

@app.route('/api/eco-tips', methods=['GET'])
def get_eco_tips():
    """Return a list of eco-friendly tips."""
    username = request.args.get('username', 'sample_user')
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"eco_tips": user_data["eco_tips"]})

@app.route('/api/community-rank', methods=['GET'])
def get_community_rank():
    """Return the user's community rank."""
    username = request.args.get('username', 'sample_user')
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"community_rank": user_data["community_rank"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5291')))
