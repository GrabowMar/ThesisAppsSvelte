from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# In-memory database (for demo purposes)
polls = []
vote_counts = {}

# Utility Functions
def find_poll(poll_id):
    for poll in polls:
        if poll['id'] == poll_id:
            return poll
    return None

def calculate_analytics(poll_id):
    poll = find_poll(poll_id)
    if not poll:
        return None
    total_votes = sum(vote_counts.get(poll_id, {}).values(), 0)
    analytics = {
        "total_votes": total_votes,
        "options": {option: vote_counts.get(poll_id, {}).get(option, 0) for option in poll['options']}
    }
    return analytics

# API Routes
@app.route('/api/polls', methods=['POST'])
def create_poll():
    data = request.json
    if not data or not 'question' in data or not 'options' in data:
        abort(400, description="Invalid request. 'question' and 'options' are required.")
    
    new_poll = {
        "id": len(polls) + 1,
        "question": data['question'],
        "options": data['options'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": data.get('expires_at', None)  # Optional: Set expiration
    }
    polls.append(new_poll)
    vote_counts[new_poll['id']] = {option: 0 for option in data['options']}
    return jsonify(new_poll), 201

@app.route('/api/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    poll = find_poll(poll_id)
    if not poll:
        abort(404, description="Poll not found.")
    return jsonify(poll)

@app.route('/api/polls/<int:poll_id>/vote', methods=['POST'])
def cast_vote(poll_id):
    data = request.json
    if not data or not 'option' in data:
        abort(400, description="Invalid request. 'option' is required.")
    
    poll = find_poll(poll_id)
    if not poll:
        abort(404, description="Poll not found.")
    if poll.get('expires_at') and datetime.now() > datetime.strptime(poll['expires_at'], "%Y-%m-%d %H:%M:%S"):
        abort(400, description="Poll has expired.")
    if data['option'] not in poll['options']:
        abort(400, description="Invalid option.")
    
    vote_counts[poll_id][data['option']] += 1
    return jsonify({"message": "Vote cast successfully."}), 200

@app.route('/api/polls/<int:poll_id>/results', methods=['GET'])
def get_results(poll_id):
    poll = find_poll(poll_id)
    if not poll:
        abort(404, description="Poll not found.")
    results = calculate_analytics(poll_id)
    return jsonify(results)

# Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5181')))