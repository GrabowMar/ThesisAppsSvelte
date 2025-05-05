# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)

class Progress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    exercise = db.relationship('Exercise', backref=db.backref('progress', lazy=True))
    date = db.Column(db.DateTime, nullable=False)
    weight_lifted = db.Column(db.Float, nullable=False)

# 4. Authentication Logic (if needed)
# For simplicity, we will not implement authentication in this example.

# 5. Utility Functions
def calculate_statistics(progress):
    total_weight_lifted = 0
    for p in progress:
        total_weight_lifted += p.weight_lifted
    return total_weight_lifted

# 6. API Routes
@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify([{'id': e.id, 'name': e.name, 'sets': e.sets, 'reps': e.reps, 'weight': e.weight} for e in exercises])

@app.route('/api/exercises', methods=['POST'])
def create_exercise():
    data = request.get_json()
    exercise = Exercise(name=data['name'], sets=data['sets'], reps=data['reps'], weight=data['weight'])
    db.session.add(exercise)
    db.session.commit()
    return jsonify({'id': exercise.id, 'name': exercise.name, 'sets': exercise.sets, 'reps': exercise.reps, 'weight': exercise.weight})

@app.route('/api/progress', methods=['GET'])
def get_progress():
    progress = Progress.query.all()
    return jsonify([{'id': p.id, 'exercise_id': p.exercise_id, 'date': p.date, 'weight_lifted': p.weight_lifted} for p in progress])

@app.route('/api/progress', methods=['POST'])
def create_progress():
    data = request.get_json()
    progress = Progress(exercise_id=data['exercise_id'], date=data['date'], weight_lifted=data['weight_lifted'])
    db.session.add(progress)
    db.session.commit()
    return jsonify({'id': progress.id, 'exercise_id': progress.exercise_id, 'date': progress.date, 'weight_lifted': progress.weight_lifted})

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    progress = Progress.query.all()
    total_weight_lifted = calculate_statistics(progress)
    return jsonify({'total_weight_lifted': total_weight_lifted})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5033')))
