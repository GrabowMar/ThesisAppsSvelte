# 1. Imports Section
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (using in-memory storage for simplicity)
reservations = {}

# 4. Authentication Logic (simple token-based auth for demonstration)
tokens = {}

# 5. Utility Functions
def generate_token():
    import secrets
    return secrets.token_hex(16)

def is_slot_available(date, time):
    return f"{date}_{time}" not in reservations

def book_slot(date, time, user):
    key = f"{date}_{time}"
    if key in reservations:
        return False
    reservations[key] = {"user": user, "timestamp": datetime.now().isoformat()}
    return True

def get_calendar():
    today = datetime.now().date()
    calendar = []
    for day in range(7):
        date = today + timedelta(days=day)
        date_str = date.strftime("%Y-%m-%d")
        day_slots = []
        for hour in range(9, 18):  # 9 AM to 5 PM
            time = f"{hour:02d}:00"
            key = f"{date_str}_{time}"
            day_slots.append({
                "time": time,
                "available": key not in reservations
            })
        calendar.append({
            "date": date_str,
            "slots": day_slots
        })
    return calendar

# 6. API Routes
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Simple authentication (replace with proper auth in production)
    if username == 'user' and password == 'password':
        token = generate_token()
        tokens[token] = username
        return jsonify({"token": token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/check_availability', methods=['POST'])
def check_availability():
    data = request.json
    date = data.get('date')
    time = data.get('time')
    
    if not date or not time:
        return jsonify({"error": "Invalid input"}), 400
    
    available = is_slot_available(date, time)
    return jsonify({"available": available}), 200

@app.route('/api/book_slot', methods=['POST'])
def book_slot_route():
    data = request.json
    date = data.get('date')
    time = data.get('time')
    token = request.headers.get('Authorization')
    
    if not date or not time or not token:
        return jsonify({"error": "Invalid input"}), 400
    
    if token not in tokens:
        return jsonify({"error": "Invalid token"}), 401
    
    user = tokens[token]
    success = book_slot(date, time, user)
    
    if success:
        return jsonify({"message": "Slot booked successfully"}), 200
    else:
        return jsonify({"error": "Slot not available"}), 400

@app.route('/api/get_calendar', methods=['GET'])
def get_calendar_route():
    calendar = get_calendar()
    return jsonify(calendar), 200

@app.route('/api/get_reservations', methods=['GET'])
def get_reservations_route():
    token = request.headers.get('Authorization')
    
    if not token or token not in tokens:
        return jsonify({"error": "Invalid token"}), 401
    
    return jsonify(reservations), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Serve the React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    html = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Reservation System</title>
      </head>
      <body>
        <div id="root"></div>
        <script type="module" src="/src/App.jsx"></script>
      </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5503')))
