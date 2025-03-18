from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity
polls = {}
votes = {}

@app.route('/create_poll', methods=['POST'])
def create_poll():
    data = request.json
    poll_id = len(polls) + 1
    polls[poll_id] = {
        'question': data['question'],
        'options': data['options'],
        'end_time': datetime.now() + timedelta(minutes=data['duration'])
    }
    votes[poll_id] = {option: 0 for option in data['options']}
    return jsonify({'poll_id': poll_id}), 201

@app.route('/polls', methods=['GET'])
def get_polls():
    return jsonify(list(polls.values())), 200

@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    if poll_id not in polls:
        return jsonify({'error': 'Poll not found'}), 404

    data = request.json
    option = data['option']

    if option not in polls[poll_id]['options']:
        return jsonify({'error': 'Invalid option'}), 400

    if datetime.now() > polls[poll_id]['end_time']:
        return jsonify({'error': 'Poll has ended'}), 400

    votes[poll_id][option] += 1
    return jsonify({'message': 'Vote cast successfully'}), 200

@app.route('/results/<int:poll_id>', methods=['GET'])
def get_results(poll_id):
    if poll_id not in polls:
        return jsonify({'error': 'Poll not found'}), 404

    return jsonify(votes[poll_id]), 200

@app.route('/analytics/<int:poll_id>', methods=['GET'])
def get_analytics(poll_id):
    if poll_id not in polls:
        return jsonify({'error': 'Poll not found'}), 404

    total_votes = sum(votes[poll_id].values())
    analytics = {
        'total_votes': total_votes,
        'results': {option: count / total_votes for option, count in votes[poll_id].items()}
    }
    return jsonify(analytics), 200

if __name__ == '__main__':
    app.run(port=5101)
