from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import datetime
app = Flask(__name__)
CORS(app)

# In-memory storage for simplicity
polls = {}
votes = {}
def get_poll_id():
    return len(polls) + 1

def get_current_time():
    return datetime.datetime.now().isoformat()
@app.route('/polls', methods=['POST'])
def create_poll():
    data = request.json
    poll_id = get_poll_id()
    polls[poll_id] = {
        'question': data['question'],
        'options': data['options'],
        'created_at': get_current_time(),
        'ends_at': data['ends_at']
    }
    votes[poll_id] = {option: 0 for option in data['options']}
    return jsonify({'poll_id': poll_id}), 201

@app.route('/polls/<int:poll_id>/vote', methods=['POST'])
def vote(poll_id):
    data = request.json
    if poll_id in polls:
        if data['option'] in polls[poll_id]['options']:
            votes[poll_id][data['option']] += 1
            return jsonify({'message': 'Vote cast successfully'}), 200
        return jsonify({'error': 'Invalid option'}), 400
    return jsonify({'error': 'Poll not found'}), 404

@app.route('/polls/<int:poll_id>/results', methods=['GET'])
def results(poll_id):
    if poll_id in polls:
        return jsonify({'results': votes[poll_id]}), 200
    return jsonify({'error': 'Poll not found'}), 404

@app.route('/polls', methods=['GET'])
def list_polls():
    return jsonify({'polls': polls}), 200
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5101')))
