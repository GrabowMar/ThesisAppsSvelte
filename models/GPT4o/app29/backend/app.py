# app/backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Database simulation - Replace or integrate with a database for production
EVENTS = []
RSVPS = []

# API Routes

@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Event Planning Platform API"})

@app.route('/api/events', methods=['GET', 'POST'])
def events():
    if request.method == 'GET':
        return jsonify(EVENTS)
    elif request.method == 'POST':
        data = request.json
        event = {
            "id": len(EVENTS) + 1,
            "name": data.get("name"),
            "date": data.get("date"),
            "budget": data.get("budget"),
            "guests": [],
            "vendors": data.get("vendors", []),
            "timeline": data.get("timeline", []),
        }
        EVENTS.append(event)
        return jsonify(event), 201

@app.route('/api/events/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def event_detail(event_id):
    event = next((e for e in EVENTS if e["id"] == event_id), None)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    if request.method == 'GET':
        return jsonify(event)
    elif request.method == 'PUT':
        data = request.json
        event.update(data)  # Update event with new data
        return jsonify(event)
    elif request.method == 'DELETE':
        EVENTS.remove(event)
        return jsonify({"message": "Event deleted"}), 200

@app.route('/api/rsvps', methods=['POST'])
def rsvp():
    data = request.json
    event_id = data.get("event_id")
    guest_name = data.get("guest_name")

    event = next((e for e in EVENTS if e["id"] == event_id), None)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    rsvp_entry = {"guest_name": guest_name, "event_id": event_id}
    event["guests"].append(guest_name)
    RSVPS.append(rsvp_entry)
    return jsonify(rsvp_entry), 201

# Start the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5297')))
