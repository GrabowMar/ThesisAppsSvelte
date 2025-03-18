from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('fitness_logger.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS workouts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  exercise TEXT, 
                  sets INTEGER, 
                  reps INTEGER, 
                  weight REAL, 
                  date TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/api/workouts', methods=['GET'])
def get_workouts():
    conn = sqlite3.connect('fitness_logger.db')
    c = conn.cursor()
    c.execute("SELECT * FROM workouts")
    workouts = c.fetchall()
    conn.close()
    return jsonify(workouts)

@app.route('/api/workouts', methods=['POST'])
def add_workout():
    data = request.get_json()
    conn = sqlite3.connect('fitness_logger.db')
    c = conn.cursor()
    c.execute("INSERT INTO workouts (exercise, sets, reps, weight, date) VALUES (?, ?, ?, ?, ?)",
              (data['exercise'], data['sets'], data['reps'], data['weight'], data['date']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Workout added successfully"}), 201

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    conn = sqlite3.connect('fitness_logger.db')
    c = conn.cursor()
    c.execute("SELECT exercise, SUM(sets * reps * weight) as total_volume FROM workouts GROUP BY exercise")
    statistics = c.fetchall()
    conn.close()
    return jsonify(statistics)

if __name__ == '__main__':
    app.run(port=5193)
