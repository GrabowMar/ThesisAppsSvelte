from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# In-memory data store for polls and votes
polls = {}
votes = {}


@app.route('/poll', methods=['POST'])
def create_poll():
    data = request.json
    if not data or 'question' not in data or 'options' not in data or 'duration' not in data:
        abort(400, description="Invalid poll data")

    poll_id = str(len(polls) + 1)
    end_time = datetime.now() + timedelta(minutes=data['duration'])
    polls[poll_id] = {
        'id': poll_id,
        'question': data['question'],
        'options': data['options'],
        'end_time': end_time.isoformat(),
        'votes': {}
    }
    votes[poll_id] = {}
    return jsonify({'poll_id': poll_id, 'end_time': end_time.isoformat()})


@app.route('/poll/<poll_id>', methods=['GET'])
def get_poll(poll_id):
    if poll_id not in polls:
        abort(404, description="Poll not found")
    return jsonify(polls[poll_id])


@app.route('/poll/<poll_id>/vote', methods=['POST'])
def cast_vote(poll_id):
    if poll_id not in polls:
        abort(404, description="Poll not found")
    data = request.json
    if not data or 'option' not in data or 'voter_id' not in data:
        abort(400, description="Invalid vote data")

    option = data['option']
    voter_id = data['voter_id']

    if datetime.now() > datetime.fromisoformat(polls[poll_id]['end_time']):
        abort(400, description="Poll has ended")

    if option not in polls[poll_id]['options']:
        abort(400, description="Invalid option")

    if poll_id in votes and voter_id in votes[poll_id]:
        abort(400, description="Voter has already voted")

    votes[poll_id][voter_id] = option
    polls[poll_id]['votes'][voter_id] = option
    return jsonify({'success': True})


@app.route('/poll/<poll_id>/results', methods=['GET'])
def get_results(poll_id):
    if poll_id not in polls:
        abort(404, description="Poll not found")

    results = {}
    for option in polls[poll_id]['options']:
        results[option] = 0

    for voter_id, option in votes[poll_id].items():
        results[option] += 1

    return jsonify(results)


@app.route('/poll/<poll_id>/analytics', methods=['GET'])
def get_analytics(poll_id):
    if poll_id not in polls:
        abort(404, description="Poll not found")

    total_votes = len(votes[poll_id])
    results = {}
    for option in polls[poll_id]['options']:
        results[option] = 0

    for voter_id, option in votes[poll_id].items():
        results[option] += 1

    analytics = {
        'total_votes': total_votes,
        'results': results
    }
    return jsonify(analytics)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5181)
