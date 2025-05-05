# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# For simplicity, we'll use in-memory storage
devices = []

# 4. Authentication Logic (if needed)
# Not implemented for simplicity, but can be added

# 5. Utility Functions
def find_device(device_id):
    return next((device for device in devices if device['id'] == device_id), None)

# 6. API Routes
@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200

@app.route('/devices', methods=['POST'])
def add_device():
    new_device = request.json
    devices.append(new_device)
    return jsonify(new_device), 201

@app.route('/devices/<int:device_id>', methods=['GET'])
def get_device(device_id):
    device = find_device(device_id)
    if device:
        return jsonify(device), 200
    return jsonify({'error': 'Device not found'}), 404

@app.route('/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    device = find_device(device_id)
    if device:
        data = request.json
        device.update(data)
        return jsonify(device), 200
    return jsonify({'error': 'Device not found'}), 404

@app.route('/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = find_device(device_id)
    if device:
        devices.remove(device)
        return jsonify({'result': 'Device deleted'}), 200
    return jsonify({'error': 'Device not found'}), 404

@app.route('/devices/<int:device_id>/status', methods=['GET'])
def get_device_status(device_id):
    device = find_device(device_id)
    if device:
        return jsonify({'status': device.get('status', 'unknown')}), 200
    return jsonify({'error': 'Device not found'}), 404

@app.route('/devices/<int:device_id>/command', methods=['POST'])
def send_command(device_id):
    device = find_device(device_id)
    if device:
        command = request.json.get('command')
        # Simulate command handling
        device['status'] = f'Executing {command}'
        return jsonify({'result': 'Command sent'}), 200
    return jsonify({'error': 'Device not found'}), 404

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5111')))
