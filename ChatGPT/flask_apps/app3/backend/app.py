from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Routes
@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    if not data.get('name') or not data.get('email') or not data.get('feedback'):
        return jsonify({"error": "All fields are required."}), 400
    
    feedback_entry = Feedback(
        name=data['name'],
        email=data['email'],
        feedback=data['feedback']
    )
    db.session.add(feedback_entry)
    db.session.commit()
    return jsonify({"message": "Feedback submitted successfully!"}), 200

@app.route('/feedback', methods=['GET'])
def get_feedback():
    feedback_list = Feedback.query.all()
    feedback_data = [{"id": fb.id, "name": fb.name, "email": fb.email, "feedback": fb.feedback} for fb in feedback_list]
    return jsonify(feedback_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
