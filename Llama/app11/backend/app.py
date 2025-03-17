# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory data store for polls
polls = {}

# Create a new poll
@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.json
    poll_id = len(polls) + 1
    polls[poll_id] = {
        'question': data['question'],
        'options': data['options'],
        'votes': {option: 0 for option in data['options']},
        'time_limit': data.get('time_limit', None)
    }
    return jsonify({'poll_id': poll_id})

# Cast a vote
@app.route('/cast_vote', methods=['POST'])
def cast_vote():
    data = request.json
    poll_id = data['poll_id']
    option = data['option']
    if poll_id in polls:
        if polls[poll_id]['time_limit'] and datetime.now() > polls[poll_id]['time_limit']:
            return jsonify({'error': 'Poll has expired'}), 400
        polls[poll_id]['votes'][option] += 1
        return jsonify({'message': 'Vote cast successfully'})
    return jsonify({'error': 'Poll not found'}), 404

# Get poll results
@app.route('/get_results', methods=['POST'])
def get_results():
    data = request.json
    poll_id = data['poll_id']
    if poll_id in polls:
        return jsonify({'results': polls[poll_id]['votes']})
    return jsonify({'error': 'Poll not found'}), 404

# Get all polls
@app.route('/get_polls', methods=['GET'])
def get_polls():
    return jsonify({'polls': polls})

if __name__ == '__main__':
    app.run(port=5021)
