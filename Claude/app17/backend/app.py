# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import uuid
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fitness.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True if os.environ.get('FLASK_ENV') == 'production' else False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
CORS(app, supports_credentials=True)

# 3. Database Models
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workouts = db.relationship('Workout', backref='user', lazy=True)
    body_stats = db.relationship('BodyStat', backref='user', lazy=True)

class Exercise(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    muscle_group = db.Column(db.String(50), nullable=True)
    workout_entries = db.relationship('WorkoutEntry', backref='exercise', lazy=True)

class Workout(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in minutes
    workout_entries = db.relationship('WorkoutEntry', backref='workout', lazy=True, cascade="all, delete-orphan")

class WorkoutEntry(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    workout_id = db.Column(db.String(36), db.ForeignKey('workout.id'), nullable=False)
    exercise_id = db.Column(db.String(36), db.ForeignKey('exercise.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

class BodyStat(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float, nullable=True)  # in kg
    body_fat = db.Column(db.Float, nullable=True)  # percentage
    muscle_mass = db.Column(db.Float, nullable=True)  # in kg
    notes = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()
    
    # Add initial exercises if none exist
    if Exercise.query.count() == 0:
        exercises = [
            {"id": str(uuid.uuid4()), "name": "Bench Press", "category": "Strength", "muscle_group": "Chest", "description": "Lie on bench and press weight upward"},
            {"id": str(uuid.uuid4()), "name": "Squat", "category": "Strength", "muscle_group": "Legs", "description": "Bend knees with weight on shoulders"},
            {"id": str(uuid.uuid4()), "name": "Deadlift", "category": "Strength", "muscle_group": "Back", "description": "Lift weight from floor to hip level"},
            {"id": str(uuid.uuid4()), "name": "Pull-up", "category": "Strength", "muscle_group": "Back", "description": "Pull body up to bar from hanging position"},
            {"id": str(uuid.uuid4()), "name": "Push-up", "category": "Strength", "muscle_group": "Chest", "description": "Push body up from prone position"},
            {"id": str(uuid.uuid4()), "name": "Running", "category": "Cardio", "muscle_group": "Legs", "description": "Run at steady pace"},
            {"id": str(uuid.uuid4()), "name": "Cycling", "category": "Cardio", "muscle_group": "Legs", "description": "Cycle at steady pace"},
            {"id": str(uuid.uuid4()), "name": "Shoulder Press", "category": "Strength", "muscle_group": "Shoulders", "description": "Press weight overhead from shoulder level"}
        ]
        
        for exercise_data in exercises:
            exercise = Exercise(**exercise_data)
            db.session.add(exercise)
        
        db.session.commit()

# 4. Authentication Logic
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 5. Utility Functions
def get_user_stats(user_id):
    # Get user's workout count
    workout_count = Workout.query.filter_by(user_id=user_id).count()
    
    # Get total exercises performed
    exercise_count = db.session.query(func.count(WorkoutEntry.id)) \
        .join(Workout) \
        .filter(Workout.user_id == user_id) \
        .scalar() or 0
    
    # Get most recent body stats
    latest_stats = BodyStat.query \
        .filter_by(user_id=user_id) \
        .order_by(BodyStat.date.desc()) \
        .first()
    
    # Get most common exercise
    most_common = db.session.query(
        Exercise.name, func.count(WorkoutEntry.id).label('count')
    ).join(WorkoutEntry).join(Workout) \
        .filter(Workout.user_id == user_id) \
        .group_by(Exercise.name) \
        .order_by(func.count(WorkoutEntry.id).desc()) \
        .first()
    
    return {
        "total_workouts": workout_count,
        "total_exercises": exercise_count,
        "current_weight": latest_stats.weight if latest_stats else None,
        "current_body_fat": latest_stats.body_fat if latest_stats else None,
        "favorite_exercise": most_common[0] if most_common else None
    }

def get_progress_data(user_id):
    # Get weight progress over time
    weight_data = db.session.query(
        BodyStat.date, BodyStat.weight
    ).filter_by(user_id=user_id) \
        .order_by(BodyStat.date.asc()) \
        .all()
    
    # Get exercise progress for a few key exercises
    bench_progress = get_exercise_progress(user_id, "Bench Press")
    squat_progress = get_exercise_progress(user_id, "Squat")
    deadlift_progress = get_exercise_progress(user_id, "Deadlift")
    
    return {
        "weight_data": [{"date": entry.date.strftime("%Y-%m-%d"), "weight": entry.weight} for entry in weight_data],
        "bench_press": bench_progress,
        "squat": squat_progress,
        "deadlift": deadlift_progress
    }

def get_exercise_progress(user_id, exercise_name):
    # Get the exercise ID
    exercise = Exercise.query.filter_by(name=exercise_name).first()
    if not exercise:
        return []
    
    # Get the progress data
    progress_data = db.session.query(
        Workout.date, 
        func.max(WorkoutEntry.weight).label('max_weight')
    ).join(WorkoutEntry) \
        .filter(Workout.user_id == user_id) \
        .filter(WorkoutEntry.exercise_id == exercise.id) \
        .group_by(Workout.date) \
        .order_by(Workout.date.asc()) \
        .all()
    
    return [{"date": entry.date.strftime("%Y-%m-%d"), "weight": entry.max_weight} for entry in progress_data]

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({"error": "All fields required"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400
        
        hashed_password = generate_password_hash(password)
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({"error": "Username and password required"}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/user', methods=['GET'])
@login_required
def get_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200

@app.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard():
    user_id = session.get('user_id')
    
    # Get recent workouts
    recent_workouts = Workout.query \
        .filter_by(user_id=user_id) \
        .order_by(Workout.date.desc()) \
        .limit(5) \
        .all()
    
    # Get user stats
    stats = get_user_stats(user_id)
    
    return jsonify({
        "recent_workouts": [
            {
                "id": workout.id,
                "name": workout.name,
                "date": workout.date.strftime("%Y-%m-%d"),
                "duration": workout.duration
            } for workout in recent_workouts
        ],
        "stats": stats
    }), 200

@app.route('/api/exercises', methods=['GET'])
@login_required
def get_exercises():
    exercises = Exercise.query.all()
    
    return jsonify([
        {
            "id": exercise.id,
            "name": exercise.name,
            "category": exercise.category,
            "muscle_group": exercise.muscle_group,
            "description": exercise.description
        } for exercise in exercises
    ]), 200

@app.route('/api/exercises/<exercise_id>', methods=['GET'])
@login_required
def get_exercise(exercise_id):
    exercise = Exercise.query.get(exercise_id)
    
    if not exercise:
        return jsonify({"error": "Exercise not found"}), 404
    
    return jsonify({
        "id": exercise.id,
        "name": exercise.name,
        "category": exercise.category,
        "muscle_group": exercise.muscle_group,
        "description": exercise.description
    }), 200

@app.route('/api/workouts', methods=['GET'])
@login_required
def get_workouts():
    user_id = session.get('user_id')
    
    workouts = Workout.query \
        .filter_by(user_id=user_id) \
        .order_by(Workout.date.desc()) \
        .all()
    
    return jsonify([
        {
            "id": workout.id,
            "name": workout.name,
            "date": workout.date.strftime("%Y-%m-%d"),
            "duration": workout.duration,
            "notes": workout.notes,
            "entry_count": len(workout.workout_entries)
        } for workout in workouts
    ]), 200

@app.route('/api/workouts', methods=['POST'])
@login_required
def create_workout():
    try:
        user_id = session.get('user_id')
        data = request.json
        
        workout = Workout(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=data.get('name'),
            date=datetime.strptime(data.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d"),
            duration=data.get('duration'),
            notes=data.get('notes')
        )
        
        db.session.add(workout)
        db.session.commit()
        
        return jsonify({
            "message": "Workout created",
            "workout": {
                "id": workout.id,
                "name": workout.name,
                "date": workout.date.strftime("%Y-%m-%d")
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/workouts/<workout_id>', methods=['GET'])
@login_required
def get_workout(workout_id):
    user_id = session.get('user_id')
    
    workout = Workout.query \
        .filter_by(id=workout_id, user_id=user_id) \
        .first()
    
    if not workout:
        return jsonify({"error": "Workout not found"}), 404
    
    entries = []
    for entry in workout.workout_entries:
        exercise = Exercise.query.get(entry.exercise_id)
        entries.append({
            "id": entry.id,
            "exercise_id": entry.exercise_id,
            "exercise_name": exercise.name,
            "sets": entry.sets,
            "reps": entry.reps,
            "weight": entry.weight,
            "notes": entry.notes
        })
    
    return jsonify({
        "id": workout.id,
        "name": workout.name,
        "date": workout.date.strftime("%Y-%m-%d"),
        "duration": workout.duration,
        "notes": workout.notes,
        "entries": entries
    }), 200

@app.route('/api/workouts/<workout_id>', methods=['DELETE'])
@login_required
def delete_workout(workout_id):
    try:
        user_id = session.get('user_id')
        
        workout = Workout.query \
            .filter_by(id=workout_id, user_id=user_id) \
            .first()
        
        if not workout:
            return jsonify({"error": "Workout not found"}), 404
        
        db.session.delete(workout)
        db.session.commit()
        
        return jsonify({"message": "Workout deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/workouts/<workout_id>/entries', methods=['POST'])
@login_required
def add_workout_entry(workout_id):
    try:
        user_id = session.get('user_id')
        
        # Verify workout belongs to user
        workout = Workout.query \
            .filter_by(id=workout_id, user_id=user_id) \
            .first()
        
        if not workout:
            return jsonify({"error": "Workout not found"}), 404
        
        data = request.json
        
        entry = WorkoutEntry(
            id=str(uuid.uuid4()),
            workout_id=workout_id,
            exercise_id=data.get('exercise_id'),
            sets=data.get('sets'),
            reps=data.get('reps'),
            weight=data.get('weight'),
            notes=data.get('notes')
        )
        
        db.session.add(entry)
        db.session.commit()
        
        exercise = Exercise.query.get(entry.exercise_id)
        
        return jsonify({
            "id": entry.id,
            "exercise_id": entry.exercise_id,
            "exercise_name": exercise.name,
            "sets": entry.sets,
            "reps": entry.reps,
            "weight": entry.weight,
            "notes": entry.notes
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/workouts/<workout_id>/entries/<entry_id>', methods=['DELETE'])
@login_required
def delete_workout_entry(workout_id, entry_id):
    try:
        user_id = session.get('user_id')
        
        # Verify workout belongs to user
        workout = Workout.query \
            .filter_by(id=workout_id, user_id=user_id) \
            .first()
        
        if not workout:
            return jsonify({"error": "Workout not found"}), 404
        
        entry = WorkoutEntry.query \
            .filter_by(id=entry_id, workout_id=workout_id) \
            .first()
        
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({"message": "Entry deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/body-stats', methods=['GET'])
@login_required
def get_body_stats():
    user_id = session.get('user_id')
    
    stats = BodyStat.query \
        .filter_by(user_id=user_id) \
        .order_by(BodyStat.date.desc()) \
        .all()
    
    return jsonify([
        {
            "id": stat.id,
            "date": stat.date.strftime("%Y-%m-%d"),
            "weight": stat.weight,
            "body_fat": stat.body_fat,
            "muscle_mass": stat.muscle_mass,
            "notes": stat.notes
        } for stat in stats
    ]), 200

@app.route('/api/body-stats', methods=['POST'])
@login_required
def add_body_stats():
    try:
        user_id = session.get('user_id')
        data = request.json
        
        # Check if stats already exist for this date
        date = datetime.strptime(data.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        existing = BodyStat.query \
            .filter_by(user_id=user_id, date=date) \
            .first()
        
        if existing:
            # Update existing stats
            existing.weight = data.get('weight', existing.weight)
            existing.body_fat = data.get('body_fat', existing.body_fat)
            existing.muscle_mass = data.get('muscle_mass', existing.muscle_mass)
            existing.notes = data.get('notes', existing.notes)
            db.session.commit()
            
            return jsonify({
                "id": existing.id,
                "date": existing.date.strftime("%Y-%m-%d"),
                "weight": existing.weight,
                "body_fat": existing.body_fat,
                "muscle_mass": existing.muscle_mass,
                "notes": existing.notes
            }), 200
        else:
            # Create new stats
            stat = BodyStat(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date,
                weight=data.get('weight'),
                body_fat=data.get('body_fat'),
                muscle_mass=data.get('muscle_mass'),
                notes=data.get('notes')
            )
            
            db.session.add(stat)
            db.session.commit()
            
            return jsonify({
                "id": stat.id,
                "date": stat.date.strftime("%Y-%m-%d"),
                "weight": stat.weight,
                "body_fat": stat.body_fat,
                "muscle_mass": stat.muscle_mass,
                "notes": stat.notes
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/progress', methods=['GET'])
@login_required
def get_progress():
    user_id = session.get('user_id')
    progress = get_progress_data(user_id)
    return jsonify(progress), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5353')))
