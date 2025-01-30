from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define database model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

# Create tables before first request
@app.before_first_request
def create_tables():
    db.create_all()

# Feedback submission route
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()

    # Validate input
    if not data.get('name') or not data.get('email') or not data.get('message') or not data.get('rating'):
        return jsonify({'error': 'All fields are required'}), 400

    # Store feedback
    feedback = Feedback(
        name=data['name'],
        email=data['email'],
        message=data['message'],
        rating=data['rating']
    )
    db.session.add(feedback)
    db.session.commit()

    return jsonify({'message': 'Feedback submitted successfully'}), 201

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
