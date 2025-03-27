from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta

# App Configuration
app = Flask(__name__)
CORS(app)

# In-memory data storage (replace with a database in production)
polls = {}
poll_id_counter = 1

# Utility Functions
def calculate_results(poll_id):
    """Calculates the results of a poll."""
    poll = polls.get(poll_id)
    if not poll:
        return {}

    total_votes = sum(poll['votes'].values())
    results = {}
    for option, votes in poll['votes'].items():
        if total_votes > 0:
            percentage = (votes / total_votes) * 100
        else:
            percentage = 0
        results[option] = {'votes': votes, 'percentage': percentage}
    return results


# API Routes
@app.route('/api/polls', methods=['GET'])
def get_polls():
    """Returns a list of all polls."""
    poll_list = []
    for poll_id, poll_data in polls.items():
        poll_list.append({
            'id': poll_id,
            'title': poll_data['title'],
            'options': list(poll_data['options']),  # Convert set to list
            'end_time': poll_data.get('end_time', None),
            'is_active': poll_data['end_time'] is None or datetime.fromisoformat(poll_data['end_time']) > datetime.now()
        })
    return jsonify(polls=poll_list)


@app.route('/api/polls', methods=['POST'])
def create_poll():
    """Creates a new poll."""
    global poll_id_counter
    data = request.get_json()
    title = data.get('title')
    options = data.get('options')
    duration = data.get('duration') # Duration in minutes

    if not title or not options or len(options) < 2:
        return jsonify({'error': 'Title and at least two options are required'}), 400

    poll_id = poll_id_counter
    poll_id_counter += 1

    new_poll = {
        'id': poll_id,
        'title': title,
        'options': set(options),
        'votes': {option: 0 for option in options},
        'created_at': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(minutes=duration)).isoformat() if duration else None, # End time if duration is provided
    }

    polls[poll_id] = new_poll

    return jsonify({'message': 'Poll created successfully', 'poll_id': poll_id}), 201



@app.route('/api/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    """Returns a specific poll by ID."""
    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404

    poll_data = {
        'id': poll['id'],
        'title': poll['title'],
        'options': list(poll['options']),  # Convert to list
        'votes': poll['votes'],
        'created_at': poll['created_at'],
        'end_time': poll.get('end_time'),
        'is_active': poll['end_time'] is None or datetime.fromisoformat(poll['end_time']) > datetime.now()
    }

    return jsonify(poll=poll_data)


@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
def vote(poll_id):
    """Casts a vote for a specific option in a poll."""
    data = request.get_json()
    option = data.get('option')

    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404

    if poll['end_time'] is not None and datetime.fromisoformat(poll['end_time']) <= datetime.now():
        return jsonify({'error': 'Poll is closed'}), 400

    if option not in poll['options']:
        return jsonify({'error': 'Invalid option'}), 400

    poll['votes'][option] += 1
    return jsonify({'message': 'Vote cast successfully'}), 200

@app.route('/api/polls/<int:poll_id>/results', methods=['GET'])
def get_results(poll_id):
    """Returns the results of a specific poll."""
    results = calculate_results(poll_id)
    if not results:
       return jsonify({'error': 'Poll not found or no votes yet'}), 404

    return jsonify(results)


# Error Handlers
@app.errorhandler(404)
def not_found(error):
    """Handles 404 errors."""
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5421')), debug=True)
