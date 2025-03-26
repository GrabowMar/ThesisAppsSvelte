# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_slot = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'Reservation({self.name}, {self.email}, {self.phone}, {self.date}, {self.time_slot})'

# 4. Authentication Logic (if needed)
# For this example, we will not include authentication logic

# 5. Utility Functions
def get_time_slots():
    time_slots = []
    for hour in range(9, 18):
        for minute in [0, 30]:
            time_slots.append(f'{hour}:{minute:02d}')
    return time_slots

def get_availability(date):
    reservations = Reservation.query.filter_by(date=date).all()
    availability = []
    time_slots = get_time_slots()
    for time_slot in time_slots:
        available = True
        for reservation in reservations:
            if reservation.time_slot == time_slot:
                available = False
                break
        availability.append((time_slot, available))
    return availability

# 6. API Routes
@app.route('/api/reserve', methods=['POST'])
def reserve():
    data = request.json
    name = data['name']
    email = data['email']
    phone = data['phone']
    date = datetime.strptime(data['date'], '%Y-%m-%d')
    time_slot = data['time_slot']
    reservation = Reservation(name=name, email=email, phone=phone, date=date, time_slot=time_slot)
    db.session.add(reservation)
    db.session.commit()
    return jsonify({'message': 'Reservation successful'}), 201

@app.route('/api/availability', methods=['GET'])
def availability():
    date = request.args.get('date')
    if date:
        date = datetime.strptime(date, '%Y-%m-%d')
        availability = get_availability(date)
        return jsonify(availability)
    return jsonify({'message': 'Date is required'}), 400

@app.route('/api/reservations', methods=['GET'])
def reservations():
    reservations = Reservation.query.all()
    data = []
    for reservation in reservations:
        data.append({
            'id': reservation.id,
            'name': reservation.name,
            'email': reservation.email,
            'phone': reservation.phone,
            'date': reservation.date.strftime('%Y-%m-%d'),
            'time_slot': reservation.time_slot
        })
    return jsonify(data)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5023')))
