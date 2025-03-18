from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory storage for reservations and time slots
reservations = {}
time_slots = [f"{9+i}:00-{10+i}:00" for i in range(12)]  # 9 AM to 9 PM

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    # Dummy login logic
    if data['username'] == 'user' and data['password'] == 'pass':
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    # Dummy registration logic
    if data['username'] and data['password']:
        return jsonify({'message': 'Registration successful'}), 200
    return jsonify({'message': 'Registration failed'}), 400

@app.route('/dashboard', methods=['GET'])
def dashboard():
    return jsonify({'message': 'Welcome to the dashboard'}), 200

@app.route('/time-slots', methods=['GET'])
def get_time_slots():
    return jsonify(time_slots), 200

@app.route('/availability', methods=['GET'])
def check_availability():
    date = request.args.get('date')
    if date in reservations:
        return jsonify({'available': False}), 200
    return jsonify({'available': True}), 200

@app.route('/reserve', methods=['POST'])
def reserve():
    data = request.json
    date = data['date']
    time_slot = data['time_slot']
    if date in reservations and reservations[date] == time_slot:
        return jsonify({'message': 'Time slot already booked'}), 400
    reservations[date] = time_slot
    return jsonify({'message': 'Reservation successful'}), 200

@app.route('/bookings', methods=['GET'])
def get_bookings():
    return jsonify(reservations), 200

if __name__ == '__main__':
    app.run(port=5103)
