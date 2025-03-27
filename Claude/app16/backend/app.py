# 1. Imports Section
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import os
import jwt
import datetime
from functools import wraps
import uuid
import time
import threading
import random
from werkzeug.security import generate_password_hash, check_password_hash

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'iot-controller-secret-key'

# 3. Database Models (simulated with in-memory storage for this example)
users = {
    'admin@example.com': {
        'password': generate_password_hash('admin123'),
        'name': 'Admin User',
        'role': 'admin'
    }
}

# Sample devices with initial states
devices = {
    'device1': {
        'id': 'device1',
        'name': 'Living Room Light',
        'type': 'light',
        'status': 'online',
        'state': False,
        'brightness': 50,
        'last_updated': time.time(),
        'data_history': [],
        'location': 'Living Room'
    },
    'device2': {
        'id': 'device2',
        'name': 'Kitchen Thermostat',
        'type': 'thermostat',
        'status': 'online',
        'temperature': 22.5,
        'target_temperature': 23,
        'last_updated': time.time(),
        'data_history': [],
        'location': 'Kitchen'
    },
    'device3': {
        'id': 'device3',
        'name': 'Front Door Lock',
        'type': 'lock',
        'status': 'online',
        'state': True,  # True = Locked
        'last_updated': time.time(),
        'data_history': [],
        'location': 'Front Door'
    }
}

automations = {
    'auto1': {
        'id': 'auto1',
        'name': 'Night Mode',
        'trigger': {
            'time': '22:00',
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        },
        'actions': [
            {'device_id': 'device1', 'property': 'state', 'value': False},
            {'device_id': 'device3', 'property': 'state', 'value': True}
        ],
        'status': 'active'
    },
    'auto2': {
        'id': 'auto2',
        'name': 'Morning Warm-up',
        'trigger': {
            'time': '06:30',
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        },
        'actions': [
            {'device_id': 'device2', 'property': 'target_temperature', 'value': 23}
        ],
        'status': 'active'
    }
}

# Device data simulation
def simulate_device_data():
    while True:
        for device_id, device in devices.items():
            # Add random variations to simulate real data
            if device['type'] == 'thermostat':
                current_temp = device['temperature']
                target_temp = device['target_temperature']
                # Temperature moves toward target with some variation
                delta = (target_temp - current_temp) * 0.1 + random.uniform(-0.3, 0.3)
                devices[device_id]['temperature'] = round(current_temp + delta, 1)
                # Save data point every minute (simulated)
                if len(device['data_history']) < 100:  # Keep last 100 points
                    device['data_history'].append({
                        'timestamp': time.time(),
                        'temperature': devices[device_id]['temperature']
                    })
                else:
                    device['data_history'].pop(0)  # Remove oldest
                    device['data_history'].append({
                        'timestamp': time.time(),
                        'temperature': devices[device_id]['temperature']
                    })
            
            # Randomly change device status occasionally
            if random.random() < 0.01:  # 1% chance
                devices[device_id]['status'] = random.choice(['online', 'offline', 'error', 'online', 'online', 'online'])
            
            devices[device_id]['last_updated'] = time.time()
        
        time.sleep(5)  # Update every 5 seconds

# Start the simulation thread
simulation_thread = threading.Thread(target=simulate_device_data, daemon=True)
simulation_thread.start()

# 4. Authentication Logic
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users.get(data['email'])
            if not current_user:
                raise jwt.InvalidTokenError
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# 5. Utility Functions
def get_device_summary():
    online_count = sum(1 for d in devices.values() if d['status'] == 'online')
    offline_count = sum(1 for d in devices.values() if d['status'] == 'offline')
    error_count = sum(1 for d in devices.values() if d['status'] == 'error')
    
    device_types = {}
    for device in devices.values():
        device_type = device['type']
        if device_type in device_types:
            device_types[device_type] += 1
        else:
            device_types[device_type] = 1
    
    return {
        'total': len(devices),
        'online': online_count,
        'offline': offline_count,
        'error': error_count,
        'types': device_types
    }

# 6. API Routes

# Authentication
@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Could not verify', 'authenticated': False}), 401
    
    user = users.get(auth.get('email'))
    
    if not user:
        return jsonify({'message': 'User not found', 'authenticated': False}), 401
    
    if check_password_hash(user['password'], auth.get('password')):
        token = jwt.encode({
            'email': auth.get('email'),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'message': 'Login successful',
            'authenticated': True,
            'token': token,
            'user': {
                'name': user['name'],
                'email': auth.get('email'),
                'role': user['role']
            }
        })
    
    return jsonify({'message': 'Invalid credentials', 'authenticated': False}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'message': 'Missing required fields', 'registered': False}), 400
    
    if data.get('email') in users:
        return jsonify({'message': 'User already exists', 'registered': False}), 409
    
    users[data.get('email')] = {
        'password': generate_password_hash(data.get('password')),
        'name': data.get('name'),
        'role': 'user'  # Default role
    }
    
    return jsonify({'message': 'User registered successfully', 'registered': True}), 201

# Dashboard & Overview
@app.route('/api/dashboard', methods=['GET'])
@token_required
def get_dashboard(current_user):
    device_summary = get_device_summary()
    recent_activity = [
        {
            'id': '1',
            'device': 'Living Room Light',
            'action': 'turned off',
            'timestamp': time.time() - 3600
        },
        {
            'id': '2',
            'device': 'Kitchen Thermostat',
            'action': 'temperature set to 23°C',
            'timestamp': time.time() - 7200
        }
    ]
    
    return jsonify({
        'device_summary': device_summary,
        'recent_activity': recent_activity,
        'automations_count': len(automations)
    })

# Devices
@app.route('/api/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    return jsonify(list(devices.values()))

@app.route('/api/devices/<device_id>', methods=['GET'])
@token_required
def get_device(current_user, device_id):
    device = devices.get(device_id)
    if not device:
        return jsonify({'message': 'Device not found'}), 404
    
    return jsonify(device)

@app.route('/api/devices/<device_id>', methods=['PUT'])
@token_required
def update_device(current_user, device_id):
    device = devices.get(device_id)
    if not device:
        return jsonify({'message': 'Device not found'}), 404
    
    data = request.json
    
    # Update allowed fields
    allowed_fields = ['name', 'location']
    for field in allowed_fields:
        if field in data:
            devices[device_id][field] = data[field]
    
    return jsonify(devices[device_id])

@app.route('/api/devices/<device_id>/command', methods=['POST'])
@token_required
def control_device(current_user, device_id):
    device = devices.get(device_id)
    if not device:
        return jsonify({'message': 'Device not found'}), 404
    
    command = request.json
    
    if not command or 'property' not in command or 'value' not in command:
        return jsonify({'message': 'Invalid command format'}), 400
    
    property_name = command['property']
    value = command['value']
    
    # Check if device supports this property
    if property_name not in device and property_name != 'state':
        return jsonify({'message': f'Property {property_name} not supported by this device'}), 400
    
    # Execute command
    devices[device_id][property_name] = value
    devices[device_id]['last_updated'] = time.time()
    
    return jsonify({
        'message': 'Command executed successfully',
        'device': devices[device_id]
    })

@app.route('/api/devices/add', methods=['POST'])
@token_required
def add_device(current_user):
    data = request.json
    
    required_fields = ['name', 'type', 'location']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    device_id = f"device{str(uuid.uuid4())[:8]}"
    
    new_device = {
        'id': device_id,
        'name': data['name'],
        'type': data['type'],
        'status': 'online',
        'last_updated': time.time(),
        'data_history': [],
        'location': data['location']
    }
    
    # Add type-specific properties
    if data['type'] == 'light':
        new_device['state'] = False
        new_device['brightness'] = 100
    elif data['type'] == 'thermostat':
        new_device['temperature'] = 21
        new_device['target_temperature'] = 21
    elif data['type'] == 'lock':
        new_device['state'] = True
    
    devices[device_id] = new_device
    
    return jsonify({
        'message': 'Device added successfully',
        'device': new_device
    }), 201

@app.route('/api/devices/<device_id>', methods=['DELETE'])
@token_required
def delete_device(current_user, device_id):
    if device_id not in devices:
        return jsonify({'message': 'Device not found'}), 404
    
    deleted_device = devices.pop(device_id)
    
    # Also remove device from automations
    for auto_id, automation in automations.items():
        automation['actions'] = [action for action in automation['actions'] 
                               if action['device_id'] != device_id]
    
    return jsonify({
        'message': 'Device deleted successfully',
        'device': deleted_device
    })

# Automations
@app.route('/api/automations', methods=['GET'])
@token_required
def get_automations(current_user):
    return jsonify(list(automations.values()))

@app.route('/api/automations/<auto_id>', methods=['GET'])
@token_required
def get_automation(current_user, auto_id):
    automation = automations.get(auto_id)
    if not automation:
        return jsonify({'message': 'Automation not found'}), 404
    
    return jsonify(automation)

@app.route('/api/automations', methods=['POST'])
@token_required
def create_automation(current_user):
    data = request.json
    
    required_fields = ['name', 'trigger', 'actions']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    if not data['actions']:
        return jsonify({'message': 'Automation must have at least one action'}), 400
    
    auto_id = f"auto{str(uuid.uuid4())[:8]}"
    
    new_automation = {
        'id': auto_id,
        'name': data['name'],
        'trigger': data['trigger'],
        'actions': data['actions'],
        'status': 'active'
    }
    
    automations[auto_id] = new_automation
    
    return jsonify({
        'message': 'Automation created successfully',
        'automation': new_automation
    }), 201

@app.route('/api/automations/<auto_id>', methods=['PUT'])
@token_required
def update_automation(current_user, auto_id):
    automation = automations.get(auto_id)
    if not automation:
        return jsonify({'message': 'Automation not found'}), 404
    
    data = request.json
    
    allowed_fields = ['name', 'trigger', 'actions', 'status']
    for field in allowed_fields:
        if field in data:
            automations[auto_id][field] = data[field]
    
    return jsonify(automations[auto_id])

@app.route('/api/automations/<auto_id>', methods=['DELETE'])
@token_required
def delete_automation(current_user, auto_id):
    if auto_id not in automations:
        return jsonify({'message': 'Automation not found'}), 404
    
    deleted_automation = automations.pop(auto_id)
    
    return jsonify({
        'message': 'Automation deleted successfully',
        'automation': deleted_automation
    })

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5351')), debug=False)
