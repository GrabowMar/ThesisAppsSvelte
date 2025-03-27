# app.py

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create database tables
with app.app_context():
    db.create_all()

# API Routes
@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Feedback App</title>
    </head>
    <body>
        <div id="root"></div>
        <script type="module" src="/src/App.jsx"></script>
    </body>
    </html>
    ''')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    new_feedback = Feedback(
        name=data.get('name', ''),
        email=data.get('email', ''),
        feedback=data.get('feedback', '')
    )
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted successfully', 'id': new_feedback.id}), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()
    return jsonify([{
        'id': f.id,
        'name': f.name,
        'email': f.email,
        'feedback': f.feedback,
        'timestamp': f.timestamp.isoformat()
    } for f in feedbacks])

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad Request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5485')))
