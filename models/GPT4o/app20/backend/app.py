from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory data storage for markers and locations
locations = []
routes = []


@app.route('/api/locations', methods=['GET'])
def get_locations():
    """
    Get all shared locations.
    """
    return jsonify({"success": True, "data": locations}), 200


@app.route('/api/locations', methods=['POST'])
def add_location():
    """
    Add a new location with data provided in the request body.
    """
    data = request.get_json()
    if not data or "name" not in data or "lat" not in data or "lng" not in data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    location = {
        "id": len(locations) + 1,
        "name": data["name"],
        "lat": data["lat"],
        "lng": data["lng"]
    }
    locations.append(location)
    return jsonify({"success": True, "message": "Location added successfully", "data": location}), 201


@app.route('/api/routes', methods=['POST'])
def add_route():
    """
    Add a new route consisting of an origin and destination.
    """
    data = request.get_json()
    if not data or "origin" not in data or "destination" not in data:
        return jsonify({"success": False, "message": "Invalid request data"}), 400

    route = {
        "id": len(routes) + 1,
        "origin": data["origin"],
        "destination": data["destination"]
    }
    routes.append(route)
    return jsonify({"success": True, "message": "Route added successfully", "data": route}), 201


@app.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.
    """
    return jsonify({"success": False, "error": "Not Found"}), 404


@app.errorhandler(500)
def server_error(error):
    """
    Handle internal server errors.
    """
    return jsonify({"success": False, "error": "Internal Server Error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5279')))
