from flask import Flask, jsonify, request, session, abort
from flask_cors import CORS
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'super_secret_key'  # In production, use environment variable

# In-memory "database" for demo purposes
teams_db = {}
players_db = {}
users_db = {}
training_sessions = []
matches = []
injuries = {}
messages = {}

# Decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            abort(401, description="Unauthorized")
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def calculate_age(dob):
    try:
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        today = datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return None

def validate_player_data(data):
    required_fields = ['name', 'position', 'dob', 'team_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    if calculate_age(data['dob']) is None:
        raise ValueError("Invalid date of birth format (use 5213-MM-DD)")
    
    if data['team_id'] not in teams_db:
        raise ValueError("Team does not exist")

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    if data['username'] in users_db:
        return jsonify({"error": "Username already exists"}), 400
    
    users_db[data['username']] = {
        'id': str(len(users_db) + 1),
        'password_hash': generate_password_hash(data['password']),
        'role': 'coach'  # Default role
    }
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    user = users_db.get(data['username'])
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({"error": "Invalid username or password"}), 401
    
    session['user_id'] = user['id']
    session['username'] = data['username']
    session['role'] = user['role']
    
    return jsonify({"message": "Logged in successfully", "user": {
        "id": user['id'],
        "username": data['username'],
        "role": user['role']
    }}), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# Team Management Routes
@app.route('/api/teams', methods=['GET', 'POST'])
@login_required
def manage_teams():
    if request.method == 'GET':
        return jsonify(list(teams_db.values())), 200
    else:
        data = request.json
        if 'name' not in data:
            return jsonify({"error": "Team name is required"}), 400
        
        team_id = str(len(teams_db) + 1)
        teams_db[team_id] = {
            'id': team_id,
            'name': data['name'],
            'sport': data.get('sport', 'Football'),
            'coach_id': session['user_id'],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify(teams_db[team_id]), 201

@app.route('/api/teams/<team_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_team(team_id):
    if team_id not in teams_db:
        return jsonify({"error": "Team not found"}), 404
    
    if request.method == 'GET':
        return jsonify(teams_db[team_id]), 200
    elif request.method == 'PUT':
        if session['user_id'] != teams_db[team_id]['coach_id']:
            return jsonify({"error": "Unauthorized to edit this team"}), 403
        
        data = request.json
        for key in ['name', 'sport']:
            if key in data:
                teams_db[team_id][key] = data[key]
        return jsonify(teams_db[team_id]), 200
    else:
        if session['user_id'] != teams_db[team_id]['coach_id']:
            return jsonify({"error": "Unauthorized to delete this team"}), 403
        
        # Remove all players from this team
        for player_id, player in players_db.items():
            if player['team_id'] == team_id:
                del players_db[player_id]
        
        del teams_db[team_id]
        return jsonify({"message": "Team deleted successfully"}), 200

# Player Management Routes
@app.route('/api/players', methods=['GET', 'POST'])
@login_required
def manage_players():
    if request.method == 'GET':
        team_id = request.args.get('team_id')
        if team_id:
            if team_id not in teams_db:
                return jsonify({"error": "Team not found"}), 404
            
            team_players = [p for p in players_db.values() if p['team_id'] == team_id]
            return jsonify(team_players), 200
        return jsonify(list(players_db.values())), 200
    else:
        try:
            data = request.json
            validate_player_data(data)
            
            player_id = str(len(players_db) + 1)
            players_db[player_id] = {
                'id': player_id,
                'team_id': data['team_id'],
                'name': data['name'],
                'position': data['position'],
                'dob': data['dob'],
                'age': calculate_age(data['dob']),
                'jersey_number': data.get('jersey_number'),
                'height': data.get('height'),
                'weight': data.get('weight'),
                'stats': {},
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            return jsonify(players_db[player_id]), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

@app.route('/api/players/<player_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_player(player_id):
    if player_id not in players_db:
        return jsonify({"error": "Player not found"}), 404
    
    team = teams_db.get(players_db[player_id]['team_id'])
    if not team or session['user_id'] != team['coach_id']:
        return jsonify({"error": "Unauthorized to manage this player"}), 403
    
    if request.method == 'GET':
        return jsonify(players_db[player_id]), 200
    elif request.method == 'PUT':
        try:
            data = request.json
            if 'team_id' in data and data['team_id'] != players_db[player_id]['team_id']:
                return jsonify({"error": "Cannot change player's team once assigned"}), 400
            
            player_data = players_db[player_id]
            for key in ['name', 'position', 'dob', 'jersey_number', 'height', 'weight']:
                if key in data:
                    player_data[key] = data[key]
                    
            # Recalculate age if DOB changed
            if 'dob' in data:
                player_data['age'] = calculate_age(data['dob'])
                
            if 'stats' in data:
                player_data['stats'].update(data['stats'])
                
            return jsonify(player_data), 200
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    else:
        del players_db[player_id]
        return jsonify({"message": "Player deleted successfully"}), 200

@app.route('/api/players/<player_id>/stats', methods=['POST'])
@login_required
def add_player_stat(player_id):
    if player_id not in players_db:
        return jsonify({"error": "Player not found"}), 404
    
    team = teams_db.get(players_db[player_id]['team_id'])
    if not team or session['user_id'] != team['coach_id']:
        return jsonify({"error": "Unauthorized to update this player's stats"}), 403
    
    data = request.json
    if not data:
        return jsonify({"error": "No stats provided"}), 400
    
    for stat, value in data.items():
        players_db[player_id]['stats'][stat] = value
    
    return jsonify(players_db[player_id]), 200

# Training Schedule Routes
@app.route('/api/training-sessions', methods=['GET', 'POST'])
@login_required
def manage_training_sessions():
    if request.method == 'GET':
        team_id = request.args.get('team_id')
        if team_id:
            if team_id not in teams_db:
                return jsonify({"error": "Team not found"}), 404
            team_sessions = [s for s in training_sessions if s['team_id'] == team_id]
            return jsonify(team_sessions), 200
        return jsonify(training_sessions), 200
    else:
        data = request.json
        if 'team_id' not in data or 'date' not in data or 'time' not in data or 'location' not in data:
            return jsonify({"error": "Team ID, date, time, and location are required"}), 400
        
        if data['team_id'] not in teams_db:
            return jsonify({"error": "Team not found"}), 404
        
        # Check if the user is the coach of this team
        team = teams_db[data['team_id']]
        if team['coach_id'] != session['user_id']:
            return jsonify({"error": "Unauthorized to create training sessions for this team"}), 403
        
        session_id = str(len(training_sessions) + 1)
        new_session = {
            'id': session_id,
            'team_id': data['team_id'],
            'date': data['date'],
            'time': data['time'],
            'location': data['location'],
            'focus_area': data.get('focus_area', 'General'),
            'notes': data.get('notes', ''),
            'created_by': session['user_id'],
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        training_sessions.append(new_session)
        return jsonify(new_session), 201

@app.route('/api/training-sessions/<session_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def manage_training_session(session_id):
    session_idx = next((i for i, s in enumerate(training_sessions) if s['id'] == session_id), None)
    if session_idx is None:
        return jsonify({"error": "Training session not found"}), 404
    
    session_record = training_sessions[session_idx]
    team = teams_db.get(session_record['team_id'])
    if not team or team['coach_id'] != session['user_id']:
        return jsonify({"error": "Unauthorized to manage this training session"}), 403
    
    if request.method == 'GET':
        return jsonify(session_record), 200
    elif request.method == 'PUT':
        data = request.json
        editable_fields = ['date', 'time', 'location', 'focus_area', 'notes']
        for field in editable_fields:
            if field in data:
                session_record[field] = data[field]
        return jsonify(session_record), 200
    else:
        training_sessions.pop(session_idx)
        return jsonify({"message": "Training session deleted successfully"}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found", "message": str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request", "message": str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5213')))
