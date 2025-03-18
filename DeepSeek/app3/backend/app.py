from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# In-memory storage for feedback submissions
feedback_store = []

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# Feedback submission endpoint
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    if not data:
        abort(400, description="Invalid data format")

    # Validate required fields
    for field in ['name', 'email', 'rating', 'comments']:
        if field not in data:
            abort(400, description=f"Missing required field: {field}")

    # Save feedback
    feedback_store.append(data)
    return jsonify({"message": "Feedback submitted successfully"})

# Retrieve all feedback submissions
@app.route('/feedback', methods=['GET'])
def get_feedback():
    return jsonify(feedback_store)

# Error handler for 400 errors
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5165)  # Backend runs on port 5165
