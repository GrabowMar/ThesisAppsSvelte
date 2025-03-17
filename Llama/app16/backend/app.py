# app.py

from flask import Flask, jsonify, request, render_template
import json

app = Flask(__name__)

# In-memory device data store (replace with a database in a real application)
devices = [
    {"id": 1, "name": "Device 1", "status": "online"},
    {"id": 2, "name": "Device 2", "status": "offline"},
    {"id": 3, "name": "Device 3", "status": "online"}
]

# Device management route
@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices)

# Status monitoring route
@app.route('/devices/<int:device_id>/status', methods=['GET'])
def get_device_status(device_id):
    device = next((device for device in devices if device["id"] == device_id), None)
    if device:
        return jsonify({"status": device["status"]})
    return jsonify({"error": "Device not found"})

# Command handling route
@app.route('/devices/<int:device_id>/command', methods=['POST'])
def send_command(device_id):
    device = next((device for device in devices if device["id"] == device_id), None)
    if device:
        command = request.json["command"]
        # Simulate command execution
        return jsonify({"result": f"Command '{command}' executed on device {device_id}"})
    return jsonify({"error": "Device not found"})

# Data processing route
@app.route('/devices/<int:device_id>/data', methods=['POST'])
def process_data(device_id):
    device = next((device for device in devices if device["id"] == device_id), None)
    if device:
        data = request.json["data"]
        # Simulate data processing
        return jsonify({"result": f"Data '{data}' processed on device {device_id}"})
    return jsonify({"error": "Device not found"})

# Simple automation route
@app.route('/automate', methods=['POST'])
def automate():
    automation_data = request.json
    # Simulate automation
    return jsonify({"result": "Automation executed successfully"})

if __name__ == '__main__':
    app.run(port=5031, debug=True)
