from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory storage for feedbacks
feedbacks = []

@app.route('/')
def index():
    return "Feedback Form Application"

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        required_fields = ['name', 'email', 'feedback']
        if not all(field in data for field in required_fields):
            return jsonify({"message": "Missing required fields"}), 400
        feedbacks.append(data)
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except Exception as e:
        return jsonify({"message": "Error submitting feedback", "error": str(e)}), 500

@app.route('/feedback', methods=['GET'])
def get_feedbacks():
    return jsonify(feedbacks), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5085)
