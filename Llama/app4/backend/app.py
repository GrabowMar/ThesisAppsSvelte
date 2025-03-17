# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage for feedback responses
feedback_responses = []

# Define a route for the root URL
@app.route('/')
def index():
    return 'Feedback Form Application'

# Define a route for submitting feedback
@app.route('/submit', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    if 'name' in data and 'email' in data and 'feedback' in data:
        feedback_responses.append(data)
        return jsonify({'message': 'Feedback submitted successfully'}), 200
    else:
        return jsonify({'message': 'Invalid feedback submission'}), 400

# Define a route for retrieving feedback responses
@app.route('/feedback', methods=['GET'])
def get_feedback():
    return jsonify(feedback_responses), 200

if __name__ == '__main__':
    app.run(port=5007)
