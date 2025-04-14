# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (in-memory for simplicity)
events = {}
guests = {}
budgets = {}
vendors = {}
rsvps = {}
invitations = {}
timelines = {}

# 4. Authentication Logic (simplified for demonstration purposes)
# In a real application, use a secure authentication mechanism

# 5. Utility Functions
def validate_event_data(data):
    required_fields = ['name', 'date', 'location']
    return all(field in data for field in required_fields)

# 6. API Routes
@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json
    if not validate_event_data(data):
        return jsonify({'error': 'Invalid event data'}), 400
    event_id = len(events) + 1
    events[event_id] = data
    return jsonify({'event_id': event_id}), 201

@app.route('/api/events', methods=['GET'])
def get_events():
    return jsonify(events)

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    return jsonify(events[event_id])

@app.route('/api/events/<int:event_id>/guests', methods=['POST'])
def add_guest(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    guest_id = len(guests) + 1
    guests[guest_id] = {'event_id': event_id, 'name': data['name'], 'email': data['email']}
    return jsonify({'guest_id': guest_id}), 201

@app.route('/api/events/<int:event_id>/guests', methods=['GET'])
def get_guests(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    event_guests = [guest for guest in guests.values() if guest['event_id'] == event_id]
    return jsonify(event_guests)

@app.route('/api/events/<int:event_id>/budget', methods=['POST'])
def set_budget(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    budgets[event_id] = data['budget']
    return jsonify({'budget': budgets[event_id]})

@app.route('/api/events/<int:event_id>/budget', methods=['GET'])
def get_budget(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    if event_id not in budgets:
        return jsonify({'error': 'Budget not set'}), 404
    return jsonify({'budget': budgets[event_id]})

@app.route('/api/events/<int:event_id>/vendors', methods=['POST'])
def add_vendor(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    vendor_id = len(vendors) + 1
    vendors[vendor_id] = {'event_id': event_id, 'name': data['name'], 'service': data['service']}
    return jsonify({'vendor_id': vendor_id}), 201

@app.route('/api/events/<int:event_id>/vendors', methods=['GET'])
def get_vendors(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    event_vendors = [vendor for vendor in vendors.values() if vendor['event_id'] == event_id]
    return jsonify(event_vendors)

@app.route('/api/events/<int:event_id>/rsvp', methods=['POST'])
def rsvp(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    rsvp_id = len(rsvps) + 1
    rsvps[rsvp_id] = {'event_id': event_id, 'guest_id': data['guest_id'], 'response': data['response']}
    return jsonify({'rsvp_id': rsvp_id}), 201

@app.route('/api/events/<int:event_id>/invitation', methods=['POST'])
def generate_invitation(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    invitation_id = len(invitations) + 1
    invitations[invitation_id] = {'event_id': event_id, 'guest_id': data['guest_id'], 'message': data['message']}
    return jsonify({'invitation_id': invitation_id}), 201

@app.route('/api/events/<int:event_id>/timeline', methods=['POST'])
def set_timeline(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    data = request.json
    timelines[event_id] = data['timeline']
    return jsonify({'timeline': timelines[event_id]})

@app.route('/api/events/<int:event_id>/timeline', methods=['GET'])
def get_timeline(event_id):
    if event_id not in events:
        return jsonify({'error': 'Event not found'}), 404
    if event_id not in timelines:
        return jsonify({'error': 'Timeline not set'}), 404
    return jsonify({'timeline': timelines[event_id]})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5057')))
