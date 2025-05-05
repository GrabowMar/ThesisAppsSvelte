# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    message = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Feedback('{self.name}', '{self.email}', '{self.message}')"

# 4. Authentication Logic (if needed)
# 5. Utility Functions
# 6. API Routes
@app.route('/api/feedback', methods=['POST'])
def create_feedback():
    data = request.get_json()
    new_feedback = Feedback(name=data['name'], email=data['email'], message=data['message'])
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback created successfully!'}), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    feedback = Feedback.query.all()
    output = []
    for feedback in feedback:
        feedback_data = {'id': feedback.id, 'name': feedback.name, 'email': feedback.email, 'message': feedback.message}
        output.append(feedback_data)
    return jsonify({'feedback': output})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5005')))
