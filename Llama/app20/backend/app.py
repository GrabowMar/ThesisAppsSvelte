from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# In-memory data store for demonstration purposes
locations = {}

# Route for frontend to get all shared locations
@app.route('/locations', methods=['GET'])
def get_locations():
    return jsonify(locations)

# Route for frontend to share a new location
@app.route('/share-location', methods=['POST'])
def share_location():
    data = request.json
    location_id = str(len(locations) + 1)
    locations[location_id] = {
        'latitude': data['latitude'],
        'longitude': data['longitude'],
        'marker': data['marker'],
        'route': data['route'],
        'shared_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify({'message': 'Location shared successfully'}), 201

# Route for frontend to search locations
@app.route('/search-locations', methods=['POST'])
def search_locations():
    data = request.json
    query = data['query']
    results = {}
    for location_id, location in locations.items():
        if query.lower() in location['marker'].lower() or query.lower() in location['route'].lower():
            results[location_id] = location
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5039)
