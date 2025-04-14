from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import secrets
from functools import wraps
import json
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = secrets.token_hex(16)

# In-memory database (for demo purposes, in production use a proper database)
users_db = {}
entries_db = {}
auth_tokens = {}
professional_resources = [
    {
        "id": 1,
        "name": "National Suicide Prevention Lifeline",
        "phone": "1-800-273-TALK (8255)",
        "website": "https://suicidepreventionlifeline.org",
        "description": "Free and confidential support for people in distress"
    },
    {
        "id": 2,
        "name": "Crisis Text Line",
        "phone": "Text HOME to 741741",
        "website": "https://www.crisistextline.org",
        "description": "Free, 24/7 support via text message"
    },
    {
        "id": 3,
        "name": "SAMHSA's National Helpline",
        "phone": "1-800-662-HELP (4357)",
        "website": "https://www.samhsa.gov/find-help/national-helpline",
        "description": "Treatment referral and information service"
    }
]

# Mock coping strategies
COPING_STRATEGIES = {
    "anxiety": [
        "Practice deep breathing exercises",
        "Try progressive muscle relaxation",
        "Go for a mindful walk",
        "Write down your worries"
    ],
    "depression": [
        "Reach out to a friend or loved one",
        "Engage in light physical activity",
        "Create a small, achievable goal for today",
        "Practice self-compassion"
    ],
    "stress": [
        "Take short breaks throughout the day",
        "Listen to calming music",
        "Try time management techniques",
        "Practice gratitude journaling"
    ]
}

# Helper functions
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({"message": "Token is missing or invalid"}), 401
            
        token = token.split(" ")[1]
        if token not in auth_tokens:
            return jsonify({"message": "Token is invalid"}), 401
            
        current_user = auth_tokens[token]
        return f(current_user, *args, **kwargs)
    return decorated

def generate_auth_token(user_id):
    token = secrets.token_hex(16)
    auth_tokens[token] = user_id
    return token

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Email and password are required"}), 400
    
    if data['email'] in users_db:
        return jsonify({"message": "User already exists"}), 409
    
    user_id = str(uuid.uuid4())
    users_db[data['email']] = {
        'id': user_id,
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'name': data.get('name', ''),
        'reminder_preferences': {
            'morning': True,
            'evening': True
        }
    }
    
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Email and password are required"}), 400
    
    user = users_db.get(data['email'])
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({"message": "Invalid credentials"}), 401
    
    token = generate_auth_token(user['id'])
    
    response = make_response(jsonify({
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name']
        }
    }))
    
    return response

@app.route('/api/logout', methods=['POST'])
@token_required
def logout(current_user):
    token = request.headers.get('Authorization').split(" ")[1]
    if token in auth_tokens:
        del auth_tokens[token]
    return jsonify({"message": "Logged out successfully"}), 200

# Mental Health Tracking Routes
@app.route('/api/entries', methods=['POST'])
@token_required
def add_entry(current_user):
    data = request.get_json()
    
    if not data or 'mood' not in data or 'stress_level' not in data:
        return jsonify({"message": "Mood and stress level are required"}), 400
    
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "user_id": current_user,
        "date": datetime.now().isoformat(),
        "mood": data['mood'],
        "stress_level": data['stress_level'],
        "journal_entry": data.get('journal_entry', ''),
        "activities": data.get('activities', [])
    }
    
    if current_user not in entries_db:
        entries_db[current_user] = []
    
    entries_db[current_user].append(entry)
    
    # Suggest coping strategies based on mood and stress
    suggestions = []
    if data['stress_level'] >= 7:
        suggestions.extend(COPING_STRATEGIES['stress'])
    if data['mood'].lower() in ['anxious', 'nervous', 'panicked']:
        suggestions.extend(COPING_STRATEGIES['anxiety'])
    elif data['mood'].lower() in ['sad', 'depressed', 'low']:
        suggestions.extend(COPING_STRATEGIES['depression'])
    
    return jsonify({
        "message": "Entry added successfully",
        "entry": entry,
        "suggestions": list(set(suggestions))[:4]  # Return unique suggestions
    }), 201

@app.route('/api/entries', methods=['GET'])
@token_required
def get_entries(current_user):
    entries = entries_db.get(current_user, [])
    
    # For demo purposes, add some sample entries if empty
    if not entries:
        sample_moods = ['happy', 'sad', 'anxious', 'calm', 'energetic']
        for i in range(5):
            entry = {
                "id": str(uuid.uuid4()),
                "user_id": current_user,
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "mood": sample_moods[i % len(sample_moods)],
                "stress_level": (i * 2) % 10,
                "journal_entry": f"Sample journal entry from day {i}",
                "activities": ["exercise", "meditation"][:i % 2 + 1]
            }
            entries.append(entry)
        entries_db[current_user] = entries
    
    return jsonify({"entries": entries})

@app.route('/api/entries/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    entries = entries_db.get(current_user, [])
    
    if not entries:
        return jsonify({
            "mood_average": 0,
            "stress_average": 0,
            "mood_distribution": {},
            "activity_frequency": {}
        })
    
    # Convert moods to numerical values for averaging (simplified example)
    mood_values = {
        'happy': 8,
        'energetic': 7,
        'calm': 6,
        'neutral': 5,
        'tired': 4,
        'anxious': 3,
        'sad': 2,
        'angry': 1
    }
    
    mood_sum = 0
    stress_sum = 0
    mood_counts = {}
    activity_counts = {}
    
    for entry in entries:
        mood = entry['mood'].lower()
        mood_sum += mood_values.get(mood, 5)
        stress_sum += entry['stress_level']
        
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        for activity in entry.get('activities', []):
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
    
    # Sort and get top activities
    top_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        "mood_average": mood_sum / len(entries),
        "stress_average": stress_sum / len(entries),
        "mood_distribution": mood_counts,
        "top_activities": [a[0] for a in top_activities]
    })

# Resources and Reminders
@app.route('/api/resources', methods=['GET'])
def get_resources():
    return jsonify({"resources": professional_resources})

@app.route('/api/reminders', methods=['GET'])
@token_required
def get_reminders(current_user):
    # Get user's reminder preferences
    user = None
    for u in users_db.values():
        if u['id'] == current_user:
            user = u
            break
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    now = datetime.now()
    next_morning = datetime(now.year, now.month, now.day, 8, 0)
    if now.hour >= 8:
        next_morning += timedelta(days=1)
    
    next_evening = datetime(now.year, now.month, now.day, 20, 0)
    if now.hour >= 20:
        next_evening += timedelta(days=1)
    
    reminders = []
    if user['reminder_preferences']['morning']:
        reminders.append({
            "type": "morning",
            "time": next_morning.isoformat(),
            "message": "Good morning! How are you feeling today?"
        })
    
    if user['reminder_preferences']['evening']:
        reminders.append({
            "type": "evening",
            "time": next_evening.isoformat(),
            "message": "How was your day? Take a moment to reflect."
        })
    
    return jsonify({"reminders": reminders})

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5209')))
