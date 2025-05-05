# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Database (for demo purposes)
devices = [
    {"id": 1, "name": "Smart Light", "status": "on"},
    {"id": 2, "name": "Thermostat", "status": "off"}
]

# 4. Utility Functions
def find_device(device_id):
    return next((device for device in devices if device["id"] == device_id), None)

# 5. API Routes
@app.route("/api/devices", methods=["GET"])
def get_devices():
    return jsonify(devices)

@app.route("/api/devices/<int:device_id>/status", methods=["GET"])
def get_device_status(device_id):
    device = find_device(device_id)
    if device:
        return jsonify({"status": device["status"]})
    return jsonify({"error": "Device not found"}), 404

@app.route("/api/devices/<int:device_id>/command", methods=["POST"])
def send_command(device_id):
    device = find_device(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    command = request.json.get("command")
    if command not in ["on", "off"]:
        return jsonify({"error": "Invalid command"}), 400

    device["status"] = command
    return jsonify({"message": f"Command '{command}' executed successfully"})

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5191")))
