from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "message": self.message}

# Initialize database
with app.app_context():
    db.create_all()

# API route to submit feedback
@app.route('/submit', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    if not data or not all(key in data for key in ['name', 'email', 'message']):
        return jsonify({"error": "Invalid input"}), 400

    feedback = Feedback(name=data['name'], email=data['email'], message=data['message'])
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"message": "Feedback submitted successfully"}), 201

# API route to fetch all feedback entries
@app.route('/feedbacks', methods=['GET'])
def get_feedbacks():
    feedback_list = Feedback.query.all()
    return jsonify([f.to_dict() for f in feedback_list]), 200

# Basic route for root
@app.route('/')
def index():
    return jsonify({"message": "Feedback Form API is running"})

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)