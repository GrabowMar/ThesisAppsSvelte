from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import re
import os

app = Flask(__name__)
CORS(app)

# In-memory storage for demonstration
feedback_storage = []

# Email validation pattern
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    
    # Validation checks
    errors = {}
    required_fields = ['name', 'email', 'rating', 'comments']
    
    for field in required_fields:
        if not data.get(field):
            errors[field] = 'This field is required'
    
    if not EMAIL_REGEX.match(data.get('email', '')):
        errors['email'] = 'Invalid email format'
    
    try:
        rating = int(data.get('rating', 0))
        if not (1 <= rating <= 5):
            errors['rating'] = 'Rating must be between 1 and 5'
    except ValueError:
        errors['rating'] = 'Invalid rating value'
    
    if errors:
        return make_response(jsonify({"errors": errors}), 400)
    
    # Store feedback
    feedback = {
        'name': data['name'],
        'email': data['email'],
        'rating': rating,
        'comments': data['comments'].strip()
    }
    feedback_storage.append(feedback)
    
    return jsonify({
        "message": "Feedback submitted successfully",
        "feedback": feedback
    }), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5565')))
