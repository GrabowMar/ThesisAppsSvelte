from flask import Flask, jsonify, request, session
from flask_cors import CORS
from datetime import datetime
import os
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # In production, use a proper secret key
CORS(app, supports_credentials=True)

# In-memory database (replace with real database in production)
users_db = {}
tracks_db = []
challenges_db = []
tips_db = [
    {"id": 1, "title": "Use reusable bags", "category": "shopping"},
    {"id": 2, "title": "Turn off lights when not in use", "category": "energy"},
    {"id": 3, "title": "Reduce meat consumption", "category": "food"},
    {"id": 4, "title": "Use public transport", "category": "transport"},
    {"id": 5, "title": "Fix leaking taps", "category": "water"}
]

def calculate_carbon_footprint(data):
    """Calculate carbon footprint based on various factors"""
    carbon_total = 0
    
    # Electricity (kgCO2 per kWh)
    if 'electricity' in data:
        carbon_total += data['electricity'] * 0.5  # Avg kg CO2 per kWh
    
    # Transportation (kgCO2 per km)
    if 'car_miles' in data:
        carbon_total += data['car_miles'] * 0.4  # Avg for gasoline car
    if 'public_transport_miles' in data:
        carbon_total += data['public_transport_miles'] * 0.1
    
    # Food (kgCO2 per meal)
    if 'meals' in data:
        carbon_total += data['meals'] * 2.5  # Avg per meal
    
    # Waste (kgCO2 per kg)
    if 'waste' in data:
        carbon_total += data['waste'] * 0.5
    
    return round(carbon_total, 2)

def validate_user_session():
    """Check if user is logged in"""
    if 'user_id' not in session or session['user_id'] not in users_db:
        return False
    return True

# User Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    
    if data['email'] in users_db:
        return jsonify({"error": "User already exists"}), 409
    
    user_id = str(uuid.uuid4())
    users_db[data['email']] = {
        'id': user_id,
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'name': data.get('name', ''),
        'join_date': datetime.now().strftime("%Y-%m-%d")
    }
    
    # Auto-login after registration
    session['user_id'] = user_id
    return jsonify({"message": "User created successfully", "user_id": user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"error": "Email and password are required"}), 400
    
    if data['email'] not in users_db:
        return jsonify({"error": "Invalid credentials"}), 401
    
    user = users_db[data['email']]
    if not check_password_hash(user['password'], data['password']):
        return jsonify({"error": "Invalid credentials"}), 401
    
    session['user_id'] = user['id']
    return jsonify({"message": "Login successful", "user": {
        "id": user['id'],
        "email": user['email'],
        "name": user['name']
    }})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/current_user', methods=['GET'])
def get_current_user():
    if not validate_user_session():
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    user = next((u for u in users_db.values() if u['id'] == user_id), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": user['id'],
        "email": user['email'],
        "name": user['name'],
        "join_date": user['join_date']
    })

# Tracking Routes
@app.route('/api/track', methods=['POST'])
def add_tracking_data():
    if not validate_user_session():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    carbon_footprint = calculate_carbon_footprint(data)
    tracking_data = {
        "id": str(uuid.uuid4()),
        "user_id": session['user_id'],
        "date": datetime.now().isoformat(),
        "data": data,
        "carbon_footprint": carbon_footprint,
        "notes": data.get('notes', '')
    }
    
    tracks_db.append(tracking_data)
    return jsonify({"message": "Data tracked successfully", "carbon_footprint": carbon_footprint}), 201

@app.route('/api/tracks', methods=['GET'])
def get_user_tracks():
    if not validate_user_session():
        return jsonify({"error": "Unauthorized"}), 401
    
    user_tracks = [t for t in tracks_db if t['user_id'] == session['user_id']]
    return jsonify({"tracks": user_tracks})

# Challenges Routes
@app.route('/api/challenges', methods=['GET'])
def get_challenges():
    community_challenges = [c for c in challenges_db if c.get('is_community', False)]
    return jsonify({"challenges": community_challenges})

@app.route('/api/challenges/create', methods=['POST'])
def create_challenge():
    if not validate_user_session():
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Title is required"}), 400
    
    challenge = {
        "id": str(uuid.uuid4()),
        "user_id": session['user_id'],
        "title": data['title'],
        "description": data.get('description', ''),
        "category": data.get('category', 'general'),
        "target": data.get('target', None),
        "start_date": datetime.now().isoformat(),
        "end_date": data.get('end_date', None),
        "is_community": data.get('is_community', False),
        "participants": [session['user_id']]
    }
    
    challenges_db.append(challenge)
    return jsonify({"message": "Challenge created successfully", "challenge": challenge}), 201

# Tips & Recommendations
@app.route('/api/tips', methods=['GET'])
def get_tips():
    category = request.args.get('category')
    if category:
        filtered_tips = [t for t in tips_db if t['category'] == category]
        return jsonify({"tips": filtered_tips})
    return jsonify({"tips": tips_db})

# Analytics
@app.route('/api/analytics", methods=['GET'])
def get_analytics():
    if not validate_user_session():
        return jsonify({"error": "Unauthorized"}), 401
    
    user_tracks = [t for t in tracks_db if t['user_id'] == session['user_id']]
    
    if not user_tracks:
        return jsonify({"error": "No tracking data found"}), 404
    
    # Calculate monthly averages
    monthly_data = {}
    for track in user_tracks:
        date = datetime.fromisoformat(track['date'])
        year_month = f"{date.year}-{date.month:02d}"
        
        if year_month not in monthly_data:
            monthly_data[year_month] = []
        monthly_data[year_month].append(track['carbon_footprint'])
    
    monthly_averages = {}
    for month, values in monthly_data.items():
        monthly_averages[month] = sum(values) / len(values)
    
    # Total footprint
    total_footprint = round(sum(t['carbon_footprint'] for t in user_tracks), 2)
    
    # Comparison with community
    community_tracks = [t for t in tracks_db if t['user_id'] != session['user_id']]
    if community_tracks:
        community_avg = sum(t['carbon_footprint'] for t in community_tracks) / len(community_tracks)
    else:
        community_avg = None
    
    return jsonify({
        "monthly_averages": monthly_averages,
        "total_footprint": total_footprint,
        "community_average": community_avg,
        "track_count": len(user_tracks)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5211')))
