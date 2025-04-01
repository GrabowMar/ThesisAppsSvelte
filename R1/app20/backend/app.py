# Backend Implementation
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Temporary in-memory storage for demonstration
locations = [
    {
        'id': 1,
        'name': 'Central Park',
        'latitude': 40.785091,
        'longitude': -73.968285,
        'created_at': datetime.now().isoformat()
    }
]

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404

# API Routes
@app.route('/api/locations', methods=['GET', 'POST'])
def handle_locations():
    if request.method == 'POST':
        data = request.json
        if not data or 'name' not in data or 'latitude' not in data or 'longitude' not in data:
            abort(400, description="Missing required fields")
            
        new_location = {
            'id': len(locations) + 1,
            'name': data['name'],
            'latitude': float(data['latitude']),
            'longitude': float(data['longitude']),
            'created_at': datetime.now().isoformat()
        }
        locations.append(new_location)
        return jsonify(new_location), 201
    
    return jsonify([loc for loc in locations])

@app.route('/api/locations/search', methods=['GET'])
def search_locations():
    query = request.args.get('q', '').lower()
    results = [loc for loc in locations if query in loc['name'].lower()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5599')))
