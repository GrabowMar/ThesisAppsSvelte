# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# 2. App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///polls.db'
db = SQLAlchemy(app)

# 3. Database Models (if needed)
class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(100), nullable=False)
    option1 = db.Column(db.String(50), nullable=False)
    option2 = db.Column(db.String(50), nullable=False)
    option1_votes = db.Column(db.Integer, default=0)
    option2_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    option = db.Column(db.String(50), nullable=False)

# 4. Authentication Logic (if needed)
# 5. Utility Functions
def create_poll(question, option1, option2, expires_in):
    poll = Poll(question=question, option1=option1, option2=option2)
    if expires_in:
        poll.expires_at = datetime.utcnow() + timedelta(minutes=expires_in)
    db.session.add(poll)
    db.session.commit()
    return poll

def cast_vote(poll_id, option):
    poll = Poll.query.get(poll_id)
    if poll:
        if option == poll.option1:
            poll.option1_votes += 1
        elif option == poll.option2:
            poll.option2_votes += 1
        db.session.commit()
        return True
    return False

def get_poll_results(poll_id):
    poll = Poll.query.get(poll_id)
    if poll:
        return {
            'option1': poll.option1,
            'option1_votes': poll.option1_votes,
            'option2': poll.option2,
            'option2_votes': poll.option2_votes
        }
    return None

# 6. API Routes
@app.route('/api/polls', methods=['POST'])
def create_poll_api():
    data = request.json
    question = data.get('question')
    option1 = data.get('option1')
    option2 = data.get('option2')
    expires_in = data.get('expires_in')
    poll = create_poll(question, option1, option2, expires_in)
    return jsonify({'id': poll.id})

@app.route('/api/polls/<int:poll_id>/votes', methods=['POST'])
def cast_vote_api(poll_id):
    data = request.json
    option = data.get('option')
    if cast_vote(poll_id, option):
        return jsonify({'message': 'Vote cast successfully'})
    return jsonify({'message': 'Failed to cast vote'}), 400

@app.route('/api/polls/<int:poll_id>/results', methods=['GET'])
def get_poll_results_api(poll_id):
    results = get_poll_results(poll_id)
    if results:
        return jsonify(results)
    return jsonify({'message': 'Poll not found'}), 404

# 7. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Not found'}), 404

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5021')))
