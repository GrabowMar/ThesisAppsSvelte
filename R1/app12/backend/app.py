# backend/app.py
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)

# In-memory database for demonstration
reservations = []
opening_hours = {'start': 9, 'end': 17}  Ứ-17 (9AM-5PM)

def is_slot_available(start_time, duration=60):
    """Check if time slot is available"""
    end_time = start_time + timedelta(minutes=duration)
    for res in reservations:
        existing_end = res['start_time'] + timedelta(minutes=res['duration'])
        if (start_time < existing_end) and (end_time > res['start_time']):
            return False
    return True

@app.route('/api/availability/<date>', methods=['GET'])
def get_availability(date):
    try:
        selected_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        abort(400, 'Invalid date format')
        
    available_slots = []
    current_time = datetime.combine(selected_date, datetime.min.time()).replace(
        hour=opening_hours['start'])
    
    while current_time.hour < opening_hours['end']:
        if is_slot_available(current_time):
            available_slots.append(current_time.strftime('%H:%M'))
        current_time += timedelta(minutes=30)
    
    return jsonify({'available_slots': available_slots})

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    data = request.get_json()
    required_fields = ['name', 'email', 'start_time', 'duration']
    if not all(field in data for field in required_fields):
        abort(400, 'Missing required fields')
    
    try:
        start_time = datetime.fromisoformat(data['start_time'])
    except ValueError:
        abort(400, 'Invalid datetime format')
    
    if not is_slot_available(start_time, data.get('duration', 60)):
        abort(409, 'Time slot no longer available')
    
    reservation = {
        'id': len(reservations) + 1,
        'name': data['name'],
        'email': data['email'],
        'start_time': start_time,
        'duration': data.get('duration', 60),
        'confirmed': False
    }
    reservations.append(reservation)
    return jsonify({'message': 'Reservation created', 'id': reservation['id']}), 201

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    return jsonify([{
        'id': r['id'],
        'start_time': r['start_time'].isoformat(),
        'duration': r['duration'],
        'name': r['name']
    } for r in reservations])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5583')))
