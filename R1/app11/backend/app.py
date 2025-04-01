from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory database
polls = []

def serialize_poll(poll):
    remaining_time = (poll['created_at'] + timedelta(hours=poll['duration']) - datetime.utcnow()).total_seconds()
    return {
        **poll,
        'created_at': poll['created_at'].isoformat(),
        'is_active': remaining_time > 0,
        'time_left': max(0, remaining_time)
    }

@app.route('/api/polls', methods=['GET', 'POST'])
def handle_polls():
    if request.method == 'POST':
        data = request.json
        new_poll = {
            'id': str(uuid.uuid4()),
            'question': data['question'],
            'options': [{'text': opt, 'votes': 0} for opt in data['options']],
            'creator': data['creator'],
            'created_at': datetime.utcnow(),
            'duration': int(data['duration'])
        }
        polls.append(new_poll)
        return jsonify(serialize_poll(new_poll)), 201
    return jsonify([serialize_poll(poll) for poll in polls])

@app.route('/api/polls/<poll_id>', methods=['GET'])
def get_poll(poll_id):
    poll = next((p for p in polls if p['id'] == poll_id), None)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404
    return jsonify(serialize_poll(poll))

@app.route('/api/polls/<poll_id>/vote', methods=['POST'])
def vote(poll_id):
    poll = next((p for p in polls if p['id'] == poll_id), None)
    if not poll:
        return jsonify({'error': 'Poll not found'}), 404
    
    remaining_time = (poll['created_at'] + timedelta(hours=poll['duration']) - datetime.utcnow()).total_seconds()
    if remaining_time <= 0:
        return jsonify({'error': 'Poll has expired'}), 400

    option_index = request.json.get('option')
    if 0 <= option_index < len(poll['options']):
        poll['options'][option_index]['votes'] += 1
        return jsonify(serialize_poll(poll))
    return jsonify({'error': 'Invalid option'}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5581')))
