# app/backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
client = MongoClient(os.getenv('MONGO_URL', 'mongodb://localhost:27017/'))
db = client['event_planner']
events_collection = db['events']

# Utility Functions
def get_next_id():
    return str(events_collection.count_documents({}) + 1)

# API Routes
@app.route('/api/events', methods=['GET'])
def get_events():
    events = list(events_collection.find({}, {'_id': 0}))
    return jsonify(events), 200

@app.route('/api/events', methods=['POST'])
def create_event():
    event = request.get_json()
    event['id'] = get_next_id()
    events_collection.insert_one(event)
    return jsonify(event), 201

@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    event = events_collection.find_one({'id': event_id}, {'_id': 0})
    if event:
        return jsonify(event), 200
    return jsonify({'error': 'Event not found'}), 404

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    event = request.get_json()
    result = events_collection.update_one({'id': event_id}, {'$set': event})
    if result.matched_count:
        return jsonify(event), 200
    return jsonify({'error': 'Event not found'}), 404

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    result = events_collection.delete_one({'id': event_id})
    if result.deleted_count:
        return jsonify({'result': True}), 200
    return jsonify({'error': 'Event not found'}), 404

# Error Handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5137')))
