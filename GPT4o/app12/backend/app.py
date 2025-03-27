# 1. IMPORTS SECTION
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta

# 2. APP CONFIGURATION
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# In-memory database (for simplicity)
reservations = {}
available_slots = {
    "Morning": ["9:00 AM", "10:00 AM"],
    "Afternoon": ["1:00 PM", "2:00 PM"],
    "Evening": ["5:00 PM", "6:00 PM"]
}

# 3. API ROUTES

## 3.1 Check Availability
@app.route('/api/availability', methods=['GET'])
def check_availability():
    date = request.args.get("date")  # Date as a string (5263-MM-DD)
    try:
        if not date:
            return jsonify({"error": "Date is required"}), 400

        # Parse date
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        # Calculate available slots by subtracting already reserved ones
        reserved_slots = reservations.get(str(parsed_date), [])
        remaining_slots = {k: [slot for slot in v if slot not in reserved_slots]
                           for k, v in available_slots.items()}
        return jsonify({"date": str(parsed_date), "slots": remaining_slots}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

## 3.2 Book Slot
@app.route('/api/reserve', methods=['POST'])
def reserve_slot():
    try:
        data = request.get_json()
        date = data.get('date')  # Date as string (5263-MM-DD)
        time_slot = data.get('timeSlot')  # Specific time slot

        if not date or not time_slot:
            return jsonify({"error": "Date and timeSlot are required"}), 400

        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Add reservation
        if str(parsed_date) not in reservations:
            reservations[str(parsed_date)] = []
        
        if time_slot in reservations[str(parsed_date)]:
            return jsonify({"error": f"Time slot {time_slot} already reserved."}), 409

        reservations[str(parsed_date)].append(time_slot)
        return jsonify({"message": f"Reservation successful for {date} at {time_slot}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

## 3.3 Get Reservations
@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    try:
        return jsonify(reservations), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. ERROR HANDLERS
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

# 5. RUNNING THE APP
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5263')))
