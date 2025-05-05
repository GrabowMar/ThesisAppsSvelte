# app/backend/app.py

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import logging

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Set up logging for production use
logging.basicConfig(level=logging.INFO)

# In-memory storage for feedback submissions.
feedbacks = []

# ------------------------------
# API Routes
# ------------------------------

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Endpoint to submit feedback.
    Expected JSON: { "name": "<name>", "email": "<email>", "message": "<feedback message>" }
    """
    data = request.get_json()
    required_fields = ['name', 'email', 'message']
    
    # Validate required fields
    if not data or not all(field in data and data[field].strip() for field in required_fields):
        app.logger.error("Validation Failed: Missing fields in submission: %s", data)
        abort(400, description="All fields (name, email, message) are required.")

    # Create a feedback record
    feedback_record = {
        'id': len(feedbacks) + 1,
        'name': data['name'].strip(),
        'email': data['email'].strip(),
        'message': data['message'].strip()
    }
    
    feedbacks.append(feedback_record)
    app.logger.info("Feedback Submitted: %s", feedback_record)
    return jsonify({"status": "success", "message": "Feedback submitted successfully."}), 201

@app.route('/api/feedback', methods=['GET'])
def get_feedbacks():
    """
    Endpoint to get all feedback submissions.
    """
    return jsonify({"feedbacks": feedbacks})

# Additional multipage sample endpoints (e.g., login, dashboard)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    # (Dummy implementation: In production, check against a database)
    if data.get("username") == "admin" and data.get("password") == "admin":
        return jsonify({"status": "success", "message": "Login successful."})
    else:
        abort(401, description="Invalid credentials.")

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    # Dummy dashboard endpoint which might include protected data.
    return jsonify({"status": "success", "data": feedbacks})

# ------------------------------
# Error Handlers
# ------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"status": "error", "message": error.description}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"status": "error", "message": error.description}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Resource not found."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal server error."}), 500

# ------------------------------
# App Runner
# ------------------------------

if __name__ == '__main__':
    # Run on host 0.0.0.0 and port 6145 as per requirements.
    port = int(os.getenv('PORT', '6145'))
    app.run(host='0.0.0.0', port=port)
