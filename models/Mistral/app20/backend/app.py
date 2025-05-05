from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
app = Flask(__name__)
CORS(app)

# Example data store for shared locations and routes
shared_locations = {}
shared_routes = {}
# For simplicity, we'll use in-memory storage.
# Authentication logic can be added here.
def get_next_id(data_store):
    return str(len(data_store) + 1)
@app.route('/api/locations', methods=['POST'])
def share_location():
    data = request.json
    location_id = get_next_id(shared_locations)
    shared_locations[location_id] = data
    return jsonify({"id": location_id}), 201

@app.route('/api/locations/<location_id>', methods=['GET'])
def get_location(location_id):
    location = shared_locations.get(location_id)
    if location:
        return jsonify(location), 200
    else:
        return jsonify({"error": "Location not found"}), 404

@app.route('/api/routes', methods=['POST'])
def share_route():
    data = request.json
    route_id = get_next_id(shared_routes)
    shared_routes[route_id] = data
    return jsonify({"id": route_id}), 201

@app.route('/api/routes/<route_id>', methods=['GET'])
def get_route(route_id):
    route = shared_routes.get(route_id)
    if route:
        return jsonify(route), 200
    else:
        return jsonify({"error": "Route not found"}), 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5119')))
