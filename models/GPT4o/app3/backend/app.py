from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# In-Memory Data Storage (Emulating a database)
feedback_data = []

# Base route for testing connection
@app.route('/')
def home():
    return jsonify({"message": "Feedback App API is running!"})

# Route to handle form submissions
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    # Extract form data sent via POST
    try:
        data = request.get_json()
        name = data.get('name', '')
        email = data.get('email', '')
        message = data.get('message', '')

        # Basic validation for empty fields
        if not name or not email or not message:
            return jsonify({"error": "All fields are required!"}), 400

        # Store the feedback in memory (simulating database storage)
        feedback_data.append({
            "name": name,
            "email": email,
            "message": message
        })

        return jsonify({"message": "Feedback submitted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to retrieve all feedback (useful for a future "dashboard" page)
@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    return jsonify({"data": feedback_data}), 200

# Error handler for 404 routes
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "The requested resource was not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5245')))
