# app/backend/app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory reservation data (replace with a database in production)
reservations = {}  # {date: {timeslot: {user: user_details}}}

# Utility Functions
def is_timeslot_available(date, timeslot):
    """Checks if a timeslot is available on a given date."""
    if date in reservations and timeslot in reservations[date]:
        return False
    return True

# API Routes

@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Returns the availability for a given date range."""
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    if not start_date_str or not end_date_str:
        return jsonify({'error': 'startDate and endDate are required'}), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use 5423-MM-DD'}), 400

    availability = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        availability[date_str] = []
        for hour in range(9, 18):  # Example: 9 AM to 5 PM slots
            timeslot = f"{hour:02d}:00-{hour+1:02d}:00"
            if is_timeslot_available(date_str, timeslot):
                availability[date_str].append(timeslot)
        current_date += timedelta(days=1)

    return jsonify(availability), 200


@app.route('/api/reserve', methods=['POST'])
def reserve_timeslot():
    """Reserves a timeslot for a given date."""
    data = request.get_json()
    date_str = data.get('date')
    timeslot = data.get('timeslot')
    user_details = data.get('user')  # e.g., {name: "John", email: "john@example.com"}

    if not date_str or not timeslot or not user_details:
        return jsonify({'error': 'Date, timeslot, and user details are required'}), 400

    if not is_timeslot_available(date_str, timeslot):
        return jsonify({'error': 'Timeslot already booked'}), 409  # Conflict

    if date_str not in reservations:
        reservations[date_str] = {}
    reservations[date_str][timeslot] = user_details

    return jsonify({'message': 'Reservation successful'}), 201  # Created


@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    """Returns all reservations (for admin purposes - secure in production)."""
    return jsonify(reservations), 200


@app.route('/api/cancel', methods=['POST'])
def cancel_reservation():
    """Cancels a reservation."""
    data = request.get_json()
    date_str = data.get('date')
    timeslot = data.get('timeslot')

    if not date_str or not timeslot:
        return jsonify({'error': 'Date and timeslot are required'}), 400

    if date_str in reservations and timeslot in reservations[date_str]:
        del reservations[date_str][timeslot]
        return jsonify({'message': 'Reservation cancelled'}), 200
    else:
        return jsonify({'error': 'Reservation not found'}), 404


# Example Authentication (Simplified) -  Expand this with a proper authentication library
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # In a real application, you'd check against a database.
    if username == "testuser" and password == "password":
        return jsonify({'message': 'Login successful', 'token': 'fake_token'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5423')), debug=True)
