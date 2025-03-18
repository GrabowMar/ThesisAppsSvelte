from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# In-memory storage for feedback
feedback_data = []

@app.route('/')
def home():
    return "Feedback Form Backend"

@app.route('/submit', methods=['POST'])
def submit_feedback():
    data = request.json

    # Simple validation
    required_fields = ['name', 'email', 'feedback']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'{field} is required'}), 400

    # Add feedback to storage
    feedback_data.append(data)
    return jsonify({'success': 'Feedback submitted successfully'}), 200

@app.route('/feedback', methods=['GET'])
def get_feedback():
    return jsonify(feedback_data), 200

if __name__ == '__main__':
    app.run(port=5087)
