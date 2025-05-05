from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Mock database for storing shared locations
locations = []

# API route to share location
@app.route('/api/share', methods=['POST'])
def share_location():
    data = request.json
    if not data or not data.get('lat') or not data.get('lng'):
        abort(400, description="Invalid location data")
    locations.append(data)
    return jsonify({"message": "Location shared successfully", "location": data}), 201

# API route to fetch all shared locations
@app.route('/api/locations', methods=['GET'])
def get_locations():
    return jsonify(locations)

# API route to search for a location using Nominatim (OpenStreetMap)
@app.route('/api/search', methods=['GET'])
def search_location():
    query = request.args.get('q')
    if not query:
        abort(400, description="Search query is required")
    response = requests.get(f"https://nominatim.openstreetmap.org/search?q={query}&format=json")
    if response.status_code != 200:
        abort(500, description="Failed to fetch search results")
    return jsonify(response.json())

# Error handler for invalid requests
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5199')))
