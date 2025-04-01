# 1. Imports Section
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import googlemaps

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this in production
jwt = JWTManager(app)

# Initialize Google Maps client
gmaps = googlemaps.Client(key='YOUR_GOOGLE_MAPS_API_KEY')  # Replace with your API key

# 3. Database Models (using in-memory storage for simplicity)
users = {}
locations = {}

# 4. Authentication Logic
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if data['username'] in users:
        return jsonify({'message': 'Username already exists'}), 400
    hashed_password = generate_password_hash(data['password'])
    users[data['username']] = {'password': hashed_password}
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = users.get(data['username'])
    if user and check_password_hash(user['password'], data['password']):
        access_token = create_access_token(identity=data['username'])
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# 5. Utility Functions
def validate_location(location):
    try:
        result = gmaps.geocode(location)
        if result:
            return result[0]['geometry']['location']
        return None
    except Exception as e:
        app.logger.error(f"Error validating location: {str(e)}")
        return None

# 6. API Routes
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Map Sharing App</title>
    </head>
    <body>
        <div id="root"></div>
        <script type="module" src="/src/App.jsx"></script>
    </body>
    </html>
    ''')

@app.route('/api/locations', methods=['POST'])
@jwt_required()
def add_location():
    data = request.json
    current_user = get_jwt_identity()
    location = validate_location(data['location'])
    if location:
        new_location = {
            'id': len(locations) + 1,
            'user': current_user,
            'location': data['location'],
            'latitude': location['lat'],
            'longitude': location['lng']
        }
        locations[new_location['id']] = new_location
        return jsonify(new_location), 201
    return jsonify({'message': 'Invalid location'}), 400

@app.route('/api/locations', methods=['GET'])
@jwt_required()
def get_locations():
    return jsonify(list(locations.values())), 200

@app.route('/api/locations/<int:location_id>', methods=['DELETE'])
@jwt_required()
def delete_location(location_id):
    current_user = get_jwt_identity()
    location = locations.get(location_id)
    if location and location['user'] == current_user:
        del locations[location_id]
        return jsonify({'message': 'Location deleted successfully'}), 200
    return jsonify({'message': 'Location not found or unauthorized'}), 404

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5519')))
