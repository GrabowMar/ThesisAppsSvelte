# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Data Storage (Replace with a real database in production)
reservations = []
time_slots = [
    {"id": 1, "start_time": "09:00", "end_time": "10:00"},
    {"id": 2, "start_time": "10:00", "end_time": "11:00"},
    {"id": 3, "start_time": "11:00", "end_time": "12:00"},
    {"id": 4, "start_time": "13:00", "end_time": "14:00"},
]

# 4. Utility Functions
def is_slot_available(slot_id):
    for reservation in reservations:
        if reservation["slot_id"] == slot_id:
            return False
    return True

# 5. API Routes
@app.route('/api/time-slots', methods=['GET'])
def get_time_slots():
    return jsonify({"time_slots": time_slots})

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    data = request.json
    slot_id = data.get("slot_id")
    name = data.get("name")

    if not slot_id or not name:
        return jsonify({"error": "Invalid input"}), 400

    if not is_slot_available(slot_id):
        return jsonify({"error": "Slot already booked"}), 400

    reservation = {"slot_id": slot_id, "name": name, "status": "confirmed"}
    reservations.append(reservation)
    return jsonify({"message": "Reservation created", "reservation": reservation}), 201

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    return jsonify({"reservations": reservations})

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5183')))
