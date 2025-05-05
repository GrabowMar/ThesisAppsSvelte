# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_should_be_changed_in_production')
db = SQLAlchemy(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class TimeSlot(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='time_slot', lazy=True)

    @property
    def formatted_date(self):
        return self.date.strftime('%Y-%m-%d')
    
    @property
    def formatted_start_time(self):
        return self.start_time.strftime('%H:%M')
    
    @property
    def formatted_end_time(self):
        return self.end_time.strftime('%H:%M')

class Reservation(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    time_slot_id = db.Column(db.String(36), db.ForeignKey('time_slot.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='confirmed')  # confirmed, cancelled, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables if they don't exist
with app.app_context():
    db.create_all()
    
    # Seed some initial time slots if none exist
    if TimeSlot.query.count() == 0:
        today = datetime.now().date()
        for i in range(14):  # Next two weeks
            current_date = today + timedelta(days=i)
            # Create 8 slots per day (9 AM to 5 PM)
            for hour in range(9, 17):
                slot = TimeSlot(
                    id=str(uuid.uuid4()),
                    date=current_date,
                    start_time=datetime.strptime(f'{hour}:00', '%H:%M').time(),
                    end_time=datetime.strptime(f'{hour+1}:00', '%H:%M').time(),
                    is_available=True
                )
                db.session.add(slot)
        db.session.commit()

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
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# 5. Utility Functions
def serialize_time_slot(time_slot):
    return {
        'id': time_slot.id,
        'date': time_slot.formatted_date,
        'start_time': time_slot.formatted_start_time,
        'end_time': time_slot.formatted_end_time,
        'is_available': time_slot.is_available
    }

def serialize_reservation(reservation):
    time_slot = reservation.time_slot
    return {
        'id': reservation.id,
        'notes': reservation.notes,
        'status': reservation.status,
        'created_at': reservation.created_at.isoformat(),
        'time_slot': {
            'id': time_slot.id,
            'date': time_slot.formatted_date,
            'start_time': time_slot.formatted_start_time,
            'end_time': time_slot.formatted_end_time
        }
    }

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} is required!'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User with this email already exists!'}), 400
    
    # Create new user
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(
        id=str(uuid.uuid4()),
        name=data['name'],
        email=data['email'],
        password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.get_json()
    
    if not auth or not auth.get('email') or not auth.get('password'):
        return jsonify({'message': 'Email and password are required!'}), 400
        
    user = User.query.filter_by(email=auth.get('email')).first()
    
    if not user:
        return jsonify({'message': 'Invalid credentials!'}), 401
        
    if check_password_hash(user.password, auth.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            }
        })
    
    return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/api/time-slots', methods=['GET'])
def get_time_slots():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = TimeSlot.query
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date >= start_date)
        except ValueError:
            return jsonify({'message': 'Invalid start_date format. Use 5343-MM-DD'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(TimeSlot.date <= end_date)
        except ValueError:
            return jsonify({'message': 'Invalid end_date format. Use 5343-MM-DD'}), 400
    
    # Default to next 7 days if no date range is provided
    if not start_date and not end_date:
        today = datetime.now().date()
        query = query.filter(TimeSlot.date >= today, 
                            TimeSlot.date <= today + timedelta(days=7))
    
    time_slots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    
    return jsonify({
        'time_slots': [serialize_time_slot(slot) for slot in time_slots]
    })

@app.route('/api/reservations', methods=['POST'])
@token_required
def create_reservation(current_user):
    data = request.get_json()
    
    if not data or not data.get('time_slot_id'):
        return jsonify({'message': 'Time slot ID is required!'}), 400
    
    time_slot = TimeSlot.query.get(data['time_slot_id'])
    
    if not time_slot:
        return jsonify({'message': 'Time slot not found!'}), 404
    
    if not time_slot.is_available:
        return jsonify({'message': 'Time slot is not available!'}), 400
    
    new_reservation = Reservation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        time_slot_id=time_slot.id,
        notes=data.get('notes', '')
    )
    
    # Update time slot availability
    time_slot.is_available = False
    
    db.session.add(new_reservation)
    db.session.commit()
    
    return jsonify({
        'message': 'Reservation created successfully!',
        'reservation': serialize_reservation(new_reservation)
    }), 201

@app.route('/api/user/reservations', methods=['GET'])
@token_required
def get_user_reservations(current_user):
    status = request.args.get('status')
    
    query = Reservation.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    reservations = query.order_by(Reservation.created_at.desc()).all()
    
    return jsonify({
        'reservations': [serialize_reservation(reservation) for reservation in reservations]
    })

@app.route('/api/reservations/<reservation_id>', methods=['PUT'])
@token_required
def update_reservation(current_user, reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    
    if not reservation:
        return jsonify({'message': 'Reservation not found or unauthorized!'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        if data['status'] == 'cancelled' and reservation.status != 'cancelled':
            # If cancelling, make the time slot available again
            time_slot = TimeSlot.query.get(reservation.time_slot_id)
            time_slot.is_available = True
        
        reservation.status = data['status']
    
    if 'notes' in data:
        reservation.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Reservation updated successfully!',
        'reservation': serialize_reservation(reservation)
    })

@app.route('/api/reservations/<reservation_id>', methods=['DELETE'])
@token_required
def delete_reservation(current_user, reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    
    if not reservation:
        return jsonify({'message': 'Reservation not found or unauthorized!'}), 404
    
    # Make time slot available again
    time_slot = TimeSlot.query.get(reservation.time_slot_id)
    time_slot.is_available = True
    
    db.session.delete(reservation)
    db.session.commit()
    
    return jsonify({'message': 'Reservation cancelled successfully!'})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found!'}), 404

@app.errorhandler(500)
def server_error(error):
    app.logger.error(f"Server error: {error}")
    return jsonify({'message': 'Internal server error!'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5343')), debug=False)
