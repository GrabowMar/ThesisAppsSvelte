# app/backend/app.py

# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Mock Database (could be extended to a real database later)
devices = [
    {"id": 1, "name": "Temperature Sensor", "status": "active", "data": {"temperature": 23.4}},
    {"id": 2, "name": "Light Monitor", "status": "inactive", "data": {"light": True}},
]

# 4. API Routes
@app.route("/api/devices", methods=["GET"])
def get_devices():
    """Fetch device list."""
    return jsonify(devices)

@app.route("/api/devices/<int:device_id>", methods=["GET"])
def get_device_status(device_id):
    """Fetch device status by ID."""
    device = next((d for d in devices if d["id"] == device_id), None)
    if device:
        return jsonify({"status": "success", "device": device})
    return jsonify({"status": "error", "message": "Device not found"}), 404

@app.route("/api/devices/<int:device_id>/toggle", methods=["POST"])
def toggle_device_state(device_id):
    """Change status of a device."""
    device = next((d for d in devices if d["id"] == device_id), None)
    if device:
        device["status"] = "active" if device["status"] == "inactive" else "inactive"
        return jsonify({"status": "success", "message": f"Device {device['name']} toggled"})
    return jsonify({"status": "error", "message": "Device not found"}), 404

@app.route("/api/devices/process", methods=["POST"])
def process_data():
    """Process and report data."""
    content = request.json
    device_id = content.get("device_id")
    command = content.get("command")

    device = next((d for d in devices if d["id"] == device_id), None)
    if device:
        # Simulate basic command handling
        result = f"Command '{command}' executed on device {device['name']}"
        return jsonify({"status": "success", "result": result})
    return jsonify({"status": "error", "message": "Device not found"}), 404

# 5. Basic Error Handling
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5271')))
