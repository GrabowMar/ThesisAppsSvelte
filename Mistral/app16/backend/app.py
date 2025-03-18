from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage for devices
devices = {}

# Route for device management (register, update, delete)
@app.route('/device', methods=['POST', 'PUT', 'DELETE'])
def manage_device():
    if request.method == 'POST':
        data = request.json
        device_id = data.get('device_id')
        if device_id in devices:
            return jsonify({"error": "Device already exists"}), 400
        devices[device_id] = data
        return jsonify({"message": "Device registered successfully"}), 201

    elif request.method == 'PUT':
        data = request.json
        device_id = data.get('device_id')
        if device_id not in devices:
            return jsonify({"error": "Device not found"}), 404
        devices[device_id] = data
        return jsonify({"message": "Device updated successfully"}), 200

    elif request.method == 'DELETE':
        device_id = request.args.get('device_id')
        if device_id not in devices:
            return jsonify({"error": "Device not found"}), 404
        del devices[device_id]
        return jsonify({"message": "Device deleted successfully"}), 200

# Route for status monitoring
@app.route('/device/<device_id>/status', methods=['GET'])
def get_device_status(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    return jsonify(devices[device_id].get('status', {}))

# Route for command handling
@app.route('/device/<device_id>/command', methods=['POST'])
def handle_command(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    command = request.json.get('command')
    # Process command (dummy implementation)
    devices[device_id]['status'] = f"Command '{command}' executed"
    return jsonify({"message": f"Command '{command}' executed successfully"}), 200

# Route for data processing
@app.route('/device/<device_id>/data', methods=['POST'])
def process_data(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    data = request.json.get('data')
    # Process data (dummy implementation)
    devices[device_id]['data'] = data
    return jsonify({"message": "Data processed successfully"}), 200

# Route for simple automation
@app.route('/device/<device_id>/automate', methods=['POST'])
def automate_device(device_id):
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    automation_rule = request.json.get('rule')
    # Apply automation rule (dummy implementation)
    devices[device_id]['automation'] = automation_rule
    return jsonify({"message": "Automation rule applied successfully"}), 200

if __name__ == '__main__':
    app.run(port=5111)
