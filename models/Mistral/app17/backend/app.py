from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS exercises (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, exercise_id INTEGER, duration INTEGER, date TEXT, FOREIGN KEY(exercise_id) REFERENCES exercises(id))''')
    conn.commit()
    conn.close()

@app.before_first_request
def initialize_database():
    init_db()

# Utility Functions
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# API Routes
@app.route('/exercises', methods=['GET'])
def get_exercises():
    conn = get_db_connection()
    exercises = conn.execute('SELECT * FROM exercises').fetchall()
    conn.close()
    return jsonify([dict(exercise) for exercise in exercises])

@app.route('/exercises', methods=['POST'])
def add_exercise():
    conn = get_db_connection()
    new_exercise = request.json
    conn.execute('INSERT INTO exercises (name, description) VALUES (?, ?)', (new_exercise['name'], new_exercise['description']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Exercise added successfully'}), 201

@app.route('/logs', methods=['POST'])
def log_workout():
    conn = get_db_connection()
    new_log = request.json
    conn.execute('INSERT INTO logs (exercise_id, duration, date) VALUES (?, ?, ?)', (new_log['exercise_id'], new_log['duration'], new_log['date']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Log added successfully'}), 201

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs').fetchall()
    conn.close()
    return jsonify([dict(log) for log in logs])

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5113')))
