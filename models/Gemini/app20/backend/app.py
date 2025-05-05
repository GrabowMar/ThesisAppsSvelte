# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json  # For handling location data
from werkzeug.exceptions import HTTPException

# 2. App Configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 3. In-Memory Data Storage (Replace with a real database for production)
locations = []
routes = []  # Store routes as a list of coordinate pairs
next_location_id = 1

# 4. Authentication Logic (Simplified - Expand for real authentication)
# NOTE: This is a placeholder.  In a real application, use a library like Flask-Login
#       and a proper user authentication system.

# 5. Utility Functions
def validate_location_data(data):
    """Validates that the location data contains latitude and longitude."""
    if not isinstance(data, dict):
        return False, "Invalid data format.  Expected a JSON object."
    if 'latitude' not in data or 'longitude' not in data:
        return False, "Latitude and longitude are required."
    try:
        float(data['latitude'])
        float(data['longitude'])
    except ValueError:
        return False, "Latitude and longitude must be numeric."
    return True, None


# 6. API Routes

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """Returns all stored locations."""
    return jsonify(locations)


@app.route('/api/locations', methods=['POST'])
def add_location():
    """Adds a new location."""
    global next_location_id
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Request body must be JSON'}), 400

    is_valid, error_message = validate_location_data(data)
    if not is_valid:
        return jsonify({'message': error_message}), 400

    new_location = {
        'id': next_location_id,
        'latitude': float(data['latitude']),
        'longitude': float(data['longitude']),
        'name': data.get('name', 'Unnamed Location'),  # Optional name
        'description': data.get('description', '')   # Optional description
    }
    locations.append(new_location)
    next_location_id += 1
    return jsonify(new_location), 201  # 201 Created


@app.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    """Returns a specific location by ID."""
    location = next((loc for loc in locations if loc['id'] == location_id), None)
    if location:
        return jsonify(location)
    return jsonify({'message': 'Location not found'}), 404


@app.route('/api/locations/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    """Deletes a location by ID."""
    global locations
    locations = [loc for loc in locations if loc['id'] != location_id]
    return jsonify({'message': 'Location deleted'}), 200

@app.route('/api/routes', methods=['POST'])
def add_route():
    """Adds a new route (list of coordinate pairs)."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({'message': 'Request body must be a list of coordinates'}), 400

    # Basic validation of coordinates
    for coord in data:
        if not isinstance(coord, list) or len(coord) != 2:
            return jsonify({'message': 'Each coordinate must be a list of [latitude, longitude]'}), 400
        try:
            float(coord[0])
            float(coord[1])
        except ValueError:
            return jsonify({'message': 'Latitude and longitude must be numeric'}), 400

    routes.append(data)  # Store the route
    return jsonify({'message': 'Route added'}), 201


@app.route('/api/routes', methods=['GET'])
def get_routes():
    """Returns all stored routes."""
    return jsonify(routes)

# 7. Error Handlers
@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5439, debug=True) # Enable debug mode during development
