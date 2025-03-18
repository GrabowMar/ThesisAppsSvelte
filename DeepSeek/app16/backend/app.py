from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Mock database for devices
devices = [
    {"id": 1, "name": "Smart Light", "status": "off"},
    {"id": 2, "name": "Thermostat", "status": "on"},
]

# Route to get all devices
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(devices)

# Route to update device status
@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    data = request.get_json()
    for device in devices:
        if device['id'] == device_id:
            device['status'] = data['status']
            return jsonify(device)
    return jsonify({"error": "Device not found"}), 404

# Route to add a new device
@app.route('/api/devices', methods=['POST'])
def add_device():
    data = request.get_json()
    new_device = {
        "id": len(devices) + 1,
        "name": data['name'],
        "status": "off",
    }
    devices.append(new_device)
    return jsonify(new_device), 201

# Route to delete a device
@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    global devices
    devices = [device for device in devices if device['id'] != device_id]
    return jsonify({"message": "Device deleted"}), 200

# Health check route
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5191)
