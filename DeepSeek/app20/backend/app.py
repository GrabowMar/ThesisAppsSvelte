from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Mock data for testing
locations = [
    {"id": 1, "name": "Central Park", "lat": 40.785091, "lng": -73.968285},
    {"id": 2, "name": "Times Square", "lat": 40.758896, "lng": -73.985130},
]

# Endpoint to get all locations
@app.route('/api/locations', methods=['GET'])
def get_locations():
    return jsonify(locations)

# Endpoint to add a new location
@app.route('/api/locations', methods=['POST'])
def add_location():
    new_location = request.get_json()
    locations.append(new_location)
    return jsonify({"message": "Location added successfully!"}), 201

# Endpoint to search for a location
@app.route('/api/locations/search', methods=['GET'])
def search_location():
    query = request.args.get('q')
    results = [loc for loc in locations if query.lower() in loc['name'].lower()]
    return jsonify(results)

# Serve the React frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5199)
