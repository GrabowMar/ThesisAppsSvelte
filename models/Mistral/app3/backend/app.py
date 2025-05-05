# 1. Imports Section
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database Models (if needed)
# 4. Authentication Logic (if needed)
# 5. Utility Functions
# 6. API Routes

@app.route('/submit', methods=['POST'])
def submit_feedback():
    data = request.json
    # Validate data
    required_fields = ['name', 'email', 'message']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'Missing {field}'}), 400

    # Process and store data (e.g., save to a database)
    # For simplicity, we'll just print it out
    print(data)

    return jsonify({'message': 'Feedback submitted successfully'}), 200

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5085')))
