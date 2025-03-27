# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-Memory Data Storage (for simplicity - replace with a database in production)
feedback_responses = []

# 5. Utility Functions (Validation Example)
def validate_feedback(data):
    """Validates the feedback data."""
    if not isinstance(data, dict):
        return False, "Invalid data format. Expected a JSON object."
    if not all(key in data for key in ["name", "email", "feedback"]):
        return False, "Missing required fields (name, email, feedback)."
    if not isinstance(data["name"], str) or not data["name"].strip():
        return False, "Name must be a non-empty string."
    if "@" not in data["email"] or "." not in data["email"]:  # Basic email validation
        return False, "Invalid email format."
    if not isinstance(data["feedback"], str) or not data["feedback"].strip():
        return False, "Feedback must be a non-empty string."

    return True, None

# 6. API Routes
@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handles feedback submission."""
    try:
        data = request.get_json()
        is_valid, error_message = validate_feedback(data)

        if not is_valid:
            return jsonify({"success": False, "message": error_message}), 400

        feedback_responses.append(data)  # Store the feedback
        print("Feedback received:", data) #logging

        return jsonify({"success": True, "message": "Feedback submitted successfully!"}), 200
    except Exception as e:
        print("Error processing feedback:", e) # Logging error
        return jsonify({"success": False, "message": "Failed to submit feedback. Please try again."}), 500

@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """Retrieves all feedback (for demonstration purposes)."""
    return jsonify(feedback_responses), 200  # Return the stored feedback

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


# 7. Error Handlers (Example - General Error Handler)
@app.errorhandler(Exception)
def handle_exception(e):
    """Handles unexpected exceptions."""
    print("Unhandled exception:", e)  # Log the exception
    return jsonify({"success": False, "message": "An unexpected error occurred."}), 500


# Basic Route example for extending multipage routing
@app.route('/api/example', methods=['GET'])
def example_route():
    return jsonify({"message": "This is an example route"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5405')))
