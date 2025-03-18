from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# In-memory storage for feedback (replace with a database in production)
feedback_data = []

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    feedback = request.json
    if not feedback or 'name' not in feedback or 'message' not in feedback:
        return jsonify({"error": "Invalid feedback data"}), 400
    
    # Validate feedback length
    if len(feedback['message']) < 10:
        return jsonify({"error": "Message must be at least 10 characters long"}), 400
    
    # Store feedback
    feedback_data.append(feedback)
    return jsonify({"message": "Feedback submitted successfully!"}), 200

@app.route('/get-feedback', methods=['GET'])
def get_feedback():
    return jsonify(feedback_data), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Replace 5000 with your backend port
