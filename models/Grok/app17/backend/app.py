# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
import os
import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_logger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# 3. Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    exercises = db.relationship('Exercise', backref='workout', lazy=True)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)

# 4. Authentication Logic
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# 5. Utility Functions
def calculate_progress(user_id):
    workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.date).all()
    if not workouts:
        return {}

    first_workout = workouts[0]
    last_workout = workouts[-1]

    progress = {}
    for exercise in first_workout.exercises:
        first_exercise = exercise
        last_exercise = next((e for e in last_workout.exercises if e.name == exercise.name), None)
        if last_exercise:
            volume_increase = (last_exercise.sets * last_exercise.reps * (last_exercise.weight or 0)) - \
                              (first_exercise.sets * first_exercise.reps * (first_exercise.weight or 0))
            progress[exercise.name] = {
                'volume_increase': volume_increase,
                'percentage_increase': (volume_increase / (first_exercise.sets * first_exercise.reps * (first_exercise.weight or 1))) * 100 if first_exercise.weight else 0
            }

    return progress

# 6. API Routes
@app.route('/workouts', methods=['POST'])
def create_workout():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    new_workout = Workout(user_id=session['user_id'])
    db.session.add(new_workout)
    db.session.commit()

    for exercise_data in data.get('exercises', []):
        new_exercise = Exercise(
            workout_id=new_workout.id,
            name=exercise_data['name'],
            sets=exercise_data['sets'],
            reps=exercise_data['reps'],
            weight=exercise_data['weight']
        )
        db.session.add(new_exercise)

    db.session.commit()
    return jsonify({'message': 'Workout logged successfully', 'workout_id': new_workout.id}), 201

@app.route('/workouts', methods=['GET'])
def get_workouts():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    workouts = Workout.query.filter_by(user_id=session['user_id']).order_by(Workout.date.desc()).all()
    workout_data = []
    for workout in workouts:
        workout_info = {
            'id': workout.id,
            'date': workout.date.isoformat(),
            'exercises': [{'name': e.name, 'sets': e.sets, 'reps': e.reps, 'weight': e.weight} for e in workout.exercises]
        }
        workout_data.append(workout_info)

    return jsonify(workout_data), 200

@app.route('/progress', methods=['GET'])
def get_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    progress = calculate_progress(session['user_id'])
    return jsonify(progress), 200

@app.route('/exercises', methods=['GET'])
def get_exercises():
    # This is a simple exercise library. In a real app, this might be more comprehensive.
    exercises = [
        {'name': 'Bench Press', 'muscle_group': 'Chest'},
        {'name': 'Squat', 'muscle_group': 'Legs'},
        {'name': 'Deadlift', 'muscle_group': 'Back'},
        {'name': 'Pull-up', 'muscle_group': 'Back'},
        {'name': 'Push-up', 'muscle_group': 'Chest'},
    ]
    return jsonify(exercises), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '6013')))
