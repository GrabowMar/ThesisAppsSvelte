# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import folium
from folium.plugins import MarkerCluster

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# For this example, we will use a simple in-memory database
locations = []

# 4. Authentication Logic (if needed)
# For this example, we will not include authentication

# 5. Utility Functions
def create_map locations):
    m = folium.Map(location=[45.5236, -122.6750])
    marker_cluster = MarkerCluster().add_to(m)
    for location in locations:
        folium.Marker(location=location['location'], popup=location['name']).add_to(marker_cluster)
    return m

# 6. API Routes
@app.route('/api/locations', methods=['GET'])
def get_locations():
    return jsonify(locations)

@app.route('/api/locations', methods=['POST'])
def create_location():
    location = request.json
    locations.append(location)
    return jsonify(location), 201

@app.route('/api/map', methods=['GET'])
def get_map():
    m = create_map(locations)
    return m._to_html()

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5039')))
