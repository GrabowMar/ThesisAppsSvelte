# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
from uuid import uuid4

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-memory Database
polls = {}

# 4. API Routes

@app.route('/api/polls', methods=['POST'])
def create_poll():
    """
    Create a new poll.
    Expected request body: {"title": str, "options": list, "duration_minutes": int}
    """
    data = request.get_json()
    if not data or 'title' not in data or 'options' not in data or 'duration_minutes' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    
    poll_id = str(uuid4())
    end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=data['duration_minutes'])
    polls[poll_id] = {
        'title': data['title'],
        'options': {option: 0 for option in data['options']},
        'end_time': end_time,
        'votes_casted': 0
    }
    return jsonify({'poll_id': poll_id}), 201

@app.route('/api/polls/<poll_id>', methods=['GET'])
def get_poll(poll_id):
    """
    Get poll details and its status.
    """
    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404
    
    is_active = datetime.datetime.utcnow() < poll['end_time']
    return jsonify({
        'poll_id': poll_id,
        'title': poll['title'],
        'options': poll['options'],
        'status': 'active' if is_active else 'closed',
        'end_time': poll['end_time'].isoformat()
    })

@app.route('/api/polls/<poll_id>/vote', methods=['POST'])
def vote_in_poll(poll_id):
    """
    Cast a vote in a poll.
    Expected request body: {"option": str}
    """
    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404

    if datetime.datetime.utcnow() > poll['end_time']:
        return jsonify({'error': 'Poll is closed'}), 403
    
    data = request.get_json()
    if not data or 'option' not in data or data['option'] not in poll['options']:
        return jsonify({'error': 'Invalid vote'}), 400
    
    poll['options'][data['option']] += 1
    poll['votes_casted'] += 1
    return jsonify({'message': 'Vote casted successfully'}), 200

@app.route('/api/polls/<poll_id>/results', methods=['GET'])
def get_poll_results(poll_id):
    """
    Get the results of a poll.
    """
    poll = polls.get(poll_id)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404

    return jsonify({'title': poll['title'], 'results': poll['options'], 'votes_casted': poll['votes_casted']}), 200

# 5. Error Handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5261)
