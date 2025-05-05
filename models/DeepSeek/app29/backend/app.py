# 1. Imports Section
from flask import Flask, jsonify, request, session, url_for
from flask_cors import CORS
import os
from datetime import datetime
import uuid
import json
import tempfile
from werkzeug.utils import secure_filename

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # For session management
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# 3. Database Models (in-memory for simplicity)
class Database:
    def __init__(self):
        self.events = {}
        self.users = {}
        self.sessions = {}
        
    def add_user(self, user_data):
        user_id = str(uuid.uuid4())
        self.users[user_id] = user_data
        return user_id
        
    def add_event(self, event_data):
        event_id = str(uuid.uuid4())
        self.events[event_id] = event_data
        return event_id
        
db = Database()

# 4. Authentication Logic
def require_auth(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# 5. Utility Functions
def validate_event_data(data):
    required_fields = ['title', 'start_date', 'end_date']
    for field in required_fields:
        if field not in data:
            return False
    return True

def generate_ical(event):
    # Simplified iCal generation
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:{event['title']}
DTSTART:{datetime.strptime(event['start_date'], '%Y-%m-%d').strftime('%Y%m%d')}
DTEND:{datetime.strptime(event['end_date'], '%Y-%m-%d').strftime('%Y%m%d')}
UID:{event['id']}@eventplanning.com
END:VEVENT
END:VCALENDAR"""

# 6. API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Invalid registration data'}), 400
        
    user_id = db.add_user({
        'email': data['email'],
        'password': data['password'],  # In prod, use proper hashing
        'name': data.get('name', '')
    })
    
    session['user_id'] = user_id
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Invalid login data'}), 400
        
    user = next((u for u in db.users.values() if u['email'] == data['email'] and u['password'] == data['password']), None)
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
        
    session['user_id'] = user
    return jsonify({'message': 'Login successful'}), 200

@app.route('/api/events', methods=['GET', 'POST'])
@require_auth
def events():
    if request.method == 'GET':
        user_events = [e for e in db.events.values() if e['organizer'] == session['user_id']]
        return jsonify(user_events)
        
    elif request.method == 'POST':
        data = request.get_json()
        if not validate_event_data(data):
            return jsonify({'error': 'Invalid event data'}), 400
            
        event_id = db.add_event({
            **data,
            'id': str(uuid.uuid4()),
            'organizer': session['user_id'],
            'guests': [],
            'budget': {'items': [], 'total': 0},
            'vendors': [],
            'timeline': [],
            'created_at': datetime.now().isoformat()
        })
        
        return jsonify({'id': event_id, 'message': 'Event created successfully'}), 201

@app.route('/api/events/<event_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def event_detail(event_id):
    if event_id not in db.events:
        return jsonify({'error': 'Event not found'}), 404
        
    event = db.events[event_id]
    
    if request.method == 'GET':
        return jsonify(event)
        
    elif request.method == 'PUT':
        data = request.get_json()
        db.events[event_id] = {**event, **data}
        return jsonify({'message': 'Event updated successfully'})
        
    elif request.method == 'DELETE':
        del db.events[event_id]
        return jsonify({'message': 'Event deleted successfully'})

@app.route('/api/events/<event_id>/invite', methods=['POST'])
@require_auth
def send_invitations(event_id):
    if event_id not in db.events:
        return jsonify({'error': 'Event not found'}), 404
        
    data = request.get_json()
    if 'emails' not in data:
        return jsonify({'error': 'No emails provided'}), 400
        
    # In a real app, this would send actual emails
    db.events[event_id]['guests'].extend([{'email': email, 'rsvp': 'pending'} for email in data['emails']])
    return jsonify({'message': 'Invitations sent successfully'})

@app.route('/api/events/<event_id>/ical', methods=['GET'])
def download_ical(event_id):
    if event_id not in db.events:
        return jsonify({'error': 'Event not found'}), 404
        
    ical_content = generate_ical(db.events[event_id])
    return jsonify({'content': ical_content})

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5217')))
