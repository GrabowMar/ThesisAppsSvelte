# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (using in-memory storage for simplicity)
polls = {}
users = {}

# 4. Authentication Logic
def authenticate_user(username, password):
    if username in users and users[username]['password'] == password:
        return True
    return False

def register_user(username, password):
    if username in users:
        return False
    users[username] = {'password': password, 'created_polls': []}
    return True

# 5. Utility Functions
def create_poll_id():
    return len(polls) + 1

def is_poll_expired(poll):
    return datetime.now() > datetime.strptime(poll['end_time'], '%Y-%m-%d %H:%M:%S')

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if authenticate_user(data['username'], data['password']):
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if register_user(data['username'], data['password']):
        return jsonify({'message': 'Registration successful'}), 201
    return jsonify({'message': 'Username already exists'}), 400

@app.route('/api/polls', methods=['POST'])
def create_poll():
    data = request.json
    poll_id = create_poll_id()
    end_time = (datetime.now() + timedelta(hours=data['duration'])).strftime('%Y-%m-%d %H:%M:%S')
    new_poll = {
        'id': poll_id,
        'question': data['question'],
        'options': data['options'],
        'votes': {option: 0 for option in data['options']},
        'created_by': data['username'],
        'end_time': end_time
    }
    polls[poll_id] = new_poll
    users[data['username']]['created_polls'].append(poll_id)
    return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201

@app.route('/api/polls', methods=['GET'])
def get_polls():
    return jsonify([poll for poll in polls.values() if not is_poll_expired(poll)]), 200

@app.route('/api/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    if poll_id not in polls:
        abort(404)
    poll = polls[poll_id]
    if is_poll_expired(poll):
        return jsonify({'message': 'Poll has expired', 'poll': poll}), 200
    return jsonify(poll), 200

@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
def vote(poll_id):
    if poll_id not in polls:
        abort(404)
    poll = polls[poll_id]
    if is_poll_expired(poll):
        return jsonify({'message': 'Cannot vote on an expired poll'}), 400
    data = request.json
    if data['option'] not in poll['options']:
        return jsonify({'message': 'Invalid option'}), 400
    poll['votes'][data['option']] += 1
    return jsonify({'message': 'Vote recorded successfully'}), 200

@app.route('/api/polls/<int:poll_id>/results', methods=['GET'])
def get_results(poll_id):
    if poll_id not in polls:
        abort(404)
    poll = polls[poll_id]
    total_votes = sum(poll['votes'].values())
    results = [{'option': option, 'votes': votes, 'percentage': (votes / total_votes * 100) if total_votes > 0 else 0} 
               for option, votes in poll['votes'].items()]
    return jsonify({'poll': poll, 'results': results}), 200

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    total_polls = len(polls)
    total_votes = sum(sum(poll['votes'].values()) for poll in polls.values())
    active_polls = sum(1 for poll in polls.values() if not is_poll_expired(poll))
    return jsonify({
        'total_polls': total_polls,
        'total_votes': total_votes,
        'active_polls': active_polls
    }), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found', 'error': 404}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'message': 'Internal server error', 'error': 500}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5501')))
