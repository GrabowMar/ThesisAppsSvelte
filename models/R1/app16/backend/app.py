# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import random
import threading
import time
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (simulated)
devices = [
    {
        "id": "1",
        "name": "Smart Thermostat",
        "type": "climate",
        "status": "online",
        "last_active": datetime.now().isoformat(),
        "temperature": 22.5
    },
    {
        "id": "2",
        "name": "Security Camera",
        "type": "security",
        "status": "offline",
        "last_active": datetime.now().isoformat(),
        "recording": False
    }
]

# 4. Automation System
def automation_task():
    while True:
        for device in devices:
            if device["type"] == "climate" and device["status"] == "online":
                device["temperature"] = round(random.uniform(18.0, 26.0), 1)
            elif device["type"] == "security":
                device["status"] = "online" if random.random() > 0.3 else "offline"
        time.sleep(10)

automation_thread = threading.Thread(target=automation_task, daemon=True)

# 5. API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify({"devices": devices})

@app.route('/api/devices', methods=['POST'])
def add_device():
    if not request.json or 'name' not in request.json or 'type' not in request.json:
        abort(400)
    
    new_device = {
        "id": str(len(devices) + 1),
        "name": request.json['name'],
        "type": request.json['type'],
        "status": "offline",
        "last_active": datetime.now().isoformat()
    }
    
    devices.append(new_device)
    return jsonify(new_device), 201

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def device_command(device_id):
    device = next((d for d in devices if d["id"] == device_id), None)
    if not device:
        abort(404)
    
    command = request.json.get('command')
    if command == "toggle":
        device["status"] = "online" if device["status"] == "offline" else "offline"
    elif device["type"] == "security" and command == "record":
        device["recording"] = not device["recording"]
    
    device["last_active"] = datetime.now().isoformat()
    return jsonify(device)

@app.route('/api/stats', methods=['GET'])
def system_stats():
    online_count = sum(1 for d in devices if d["status"] == "online")
    return jsonify({
        "total_devices": len(devices),
        "online_devices": online_count,
        "update_time": datetime.now().isoformat()
    })

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    automation_thread.start()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5591')))
