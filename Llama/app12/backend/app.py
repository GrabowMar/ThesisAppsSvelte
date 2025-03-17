from flask import Flask, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory data store for demonstration purposes
reservations = {}

# Generate a unique ID for each reservation
def generate_id():
    return len(reservations) + 1

# Availability check endpoint
@app.route('/availability', methods=['GET'])
def check_availability():
    date = request.args.get('date')
    time_slot = request.args.get('time_slot')
    
    if date and time_slot:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            time_slot_obj = datetime.strptime(time_slot, '%H:%M')
            date_time_obj = datetime.combine(date_obj.date(), time_slot_obj.time())
            
            if date_time_obj in reservations.values():
                return jsonify({'available': False})
            else:
                return jsonify({'available': True})
        except ValueError:
            return jsonify({'error': 'Invalid date or time format'}), 400
    else:
        return jsonify({'error': 'Missing date or time slot'}), 400

# Reservation endpoint
@app.route('/reserve', methods=['POST'])
def make_reservation():
    data = request.json
    name = data.get('name')
    date = data.get('date')
    time_slot = data.get('time_slot')
    
    if name and date and time_slot:
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            time_slot_obj = datetime.strptime(time_slot, '%H:%M')
            date_time_obj = datetime.combine(date_obj.date(), time_slot_obj.time())
            
            if date_time_obj in reservations.values():
                return jsonify({'error': 'Time slot already reserved'}), 400
            else:
                reservation_id = generate_id()
                reservations[reservation_id] = date_time_obj
                
                return jsonify({'reservation_id': reservation_id, 'name': name, 'date': date, 'time_slot': time_slot})
        except ValueError:
            return jsonify({'error': 'Invalid date or time format'}), 400
    else:
        return jsonify({'error': 'Missing required fields'}), 400

# Reservation management endpoint
@app.route('/reservations', methods=['GET'])
def get_reservations():
    return jsonify(list(reservations.values()))

if __name__ == '__main__':
    app.run(port=5023)
