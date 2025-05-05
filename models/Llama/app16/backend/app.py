# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# For this example, we'll use a simple in-memory dictionary to store device data
devices = {
    "device1": {"status": "online", "data": {"temperature": 25, "humidity": 60}},
    "device2": {"status": "offline", "data": {"temperature": 20, "humidity": 50}}
}

# 4. Authentication Logic (if needed)
# For this example, we'll use a simple authentication system with a single user
users = {
    "admin": {"password": "password123"}
}

# 5. Utility Functions
def get_device_status(device_id):
    return devices.get(device_id, {"status": "unknown"})

def update_device_status(device_id, status):
    devices[device_id] = {"status": status, "data": devices.get(device_id, {}).get("data", {})}
    return devices[device_id]

# 6. API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(devices)

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    return jsonify(get_device_status(device_id))

@app.route('/api/devices/<device_id>/status', methods=['PUT'])
def update_device(device_id):
    data = request.get_json()
    if 'status' in data:
        return jsonify(update_device_status(device_id, data['status']))
    else:
        return jsonify({"error": "Missing status field"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if 'username' in data and 'password' in data:
        if data['username'] in users and users[data['username']]['password'] == data['password']:
            return jsonify({"token": "dummy_token"})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    else:
        return jsonify({"error": "Missing username or password"}), 400

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5031')))
