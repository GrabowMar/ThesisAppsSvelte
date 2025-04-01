# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os
import json
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # For session management

# 3. Database Models (simplified in-memory storage for demonstration)
devices = {
    "device1": {"status": "on", "last_updated": datetime.now().isoformat()},
    "device2": {"status": "off", "last_updated": datetime.now().isoformat()},
}

# 4. Authentication Logic
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data.get('username') == 'admin' and data.get('password') == 'password':
        session['logged_in'] = True
        return jsonify({"message": "Logged in successfully"}), 200
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({"message": "Logged out successfully"}), 200

# 5. Utility Functions
def update_device_status(device_id, status):
    if device_id in devices:
        devices[device_id]['status'] = status
        devices[device_id]['last_updated'] = datetime.now().isoformat()
        return True
    return False

# 6. API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    if device_id in devices:
        return jsonify(devices[device_id]), 200
    return jsonify({"message": "Device not found"}), 404

@app.route('/api/devices/<device_id>/status', methods=['PUT'])
def update_device(device_id):
    if 'logged_in' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    data = request.json
    status = data.get('status')
    if status in ['on', 'off']:
        if update_device_status(device_id, status):
            return jsonify({"message": "Device status updated"}), 200
        return jsonify({"message": "Device not found"}), 404
    return jsonify({"message": "Invalid status"}), 400

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_command(device_id):
    if 'logged_in' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    data = request.json
    command = data.get('command')
    if command:
        # In a real scenario, this would send the command to the device
        return jsonify({"message": f"Command '{command}' sent to {device_id}"}), 200
    return jsonify({"message": "Invalid command"}), 400

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5511')))
