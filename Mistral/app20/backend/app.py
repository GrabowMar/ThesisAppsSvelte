from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Dummy data for locations
locations = [
    {"id": 1, "name": "Location 1", "lat": 34.0522, "lng": -118.2437, "description": "First location"},
    {"id": 2, "name": "Location 2", "lat": 40.7128, "lng": -74.0060, "description": "Second location"},
]

# Route to get all locations
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(locations)

# Route to get a specific location by ID
@app.route('/locations/<int:id>', methods=['GET'])
def get_location(id):
    location = next((loc for loc in locations if loc['id'] == id), None)
    if location:
        return jsonify(location)
    return jsonify({"error": "Location not found"}), 404

# Route to add a new location
@app.route('/locations', methods=['POST'])
def add_location():
    new_location = request.json
    new_location['id'] = len(locations) + 1
    locations.append(new_location)
    return jsonify(new_location), 201

# Route to update an existing location
@app.route('/locations/<int:id>', methods=['PUT'])
def update_location(id):
    location = next((loc for loc in locations if loc['id'] == id), None)
    if location:
        updated_data = request.json
        location.update(updated_data)
        return jsonify(location)
    return jsonify({"error": "Location not found"}), 404

# Route to delete a location
@app.route('/locations/<int:id>', methods=['DELETE'])
def delete_location(id):
    global locations
    locations = [loc for loc in locations if loc['id'] != id]
    return jsonify({"success": "Location deleted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5119)
