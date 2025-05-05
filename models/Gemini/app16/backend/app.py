# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import datetime  # For timestamping data

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'  # Add a secret key for security

# 3. Dummy Device Data (In-memory for simplicity)
devices = {
    "device1": {"name": "Temperature Sensor", "status": "online", "temperature": 25.5, "humidity": 60},
    "device2": {"name": "Smart Switch", "status": "offline", "power": "off"},
}

# 4. Utility Functions
def log_event(device_id, event_type, message):
    """Logs events with timestamp."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] Device: {device_id} - {event_type}: {message}")

# 5. API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Returns a list of all devices and their details."""
    return jsonify(devices)

@app.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """Returns details of a specific device."""
    if device_id in devices:
        return jsonify(devices[device_id])
    else:
        log_event(device_id, "ERROR", "Device not found")
        return jsonify({"error": "Device not found"}), 404

@app.route('/api/devices/<device_id>/control', methods=['POST'])
def control_device(device_id):
    """Controls a device (e.g., turn on/off, set temperature)."""
    if device_id not in devices:
        log_event(device_id, "ERROR", "Device not found")
        return jsonify({"error": "Device not found"}), 404

    data = request.get_json()
    if not data:
        log_event(device_id, "ERROR", "Invalid request data")
        return jsonify({"error": "Invalid request data"}), 400

    try:
        # Example: Assuming the request has a 'command' field
        command = data.get('command')

        if device_id == "device1":  # Temperature Sensor
            if command == "get_reading":
                 devices[device_id]["temperature"] += 0.1
                 devices[device_id]["humidity"] += 0.1
                 log_event(device_id, "INFO", f"Getting current reading: Temp={devices[device_id]['temperature']}, Humidity={devices[device_id]['humidity']}")
                 return jsonify({"message": "Reading updated!", "temperature": devices[device_id]["temperature"], "humidity": devices[device_id]["humidity"]})
            else:
                log_event(device_id, "ERROR", f"Invalid command: {command}")
                return jsonify({"error": "Invalid command"}), 400
        elif device_id == "device2":  # Smart Switch
            if command == "toggle":
                devices[device_id]["power"] = "on" if devices[device_id]["power"] == "off" else "off"
                log_event(device_id, "INFO", f"Power toggled to {devices[device_id]['power']}")
                return jsonify({"message": f"Power toggled to {devices[device_id]['power']}"})
            else:
                log_event(device_id, "ERROR", f"Invalid command: {command}")
                return jsonify({"error": "Invalid command"}), 400
        else:
             return jsonify({"error": "Device type not recognized"}), 400
    except Exception as e:
        log_event(device_id, "ERROR", f"Error processing command: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices/<device_id>/status', methods=['PUT'])
def update_device_status(device_id):
    """Updates the status of a device (e.g., online/offline)."""
    if device_id not in devices:
        log_event(device_id, "ERROR", "Device not found")
        return jsonify({"error": "Device not found"}), 404

    data = request.get_json()
    if not data or 'status' not in data:
        log_event(device_id, "ERROR", "Invalid status data")
        return jsonify({"error": "Invalid status data"}), 400

    status = data['status']
    devices[device_id]["status"] = status
    log_event(device_id, "INFO", f"Status updated to {status}")
    return jsonify({"message": f"Status updated to {status}"})

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    log_event("GLOBAL", "ERROR", "Resource not found")
    return jsonify({"error": "Not found"}), 404

# 7. Authentication Routes (basic example)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data and data.get('username') == 'admin' and data.get('password') == 'password':  #Replace with secure authentication
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/register', methods=['POST'])
def register():
     data = request.get_json()
     if data and data.get('username') and data.get('password'):
          return jsonify({"message": "Registration successful"}) #Replace with secure registration
     else:
          return jsonify({"error": "Invalid registration data"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5431')))
