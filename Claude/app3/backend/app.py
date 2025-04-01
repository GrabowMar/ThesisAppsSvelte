# 1. Imports Section
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import os
import json
from datetime import datetime
import uuid
from functools import wraps

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Simple file-based storage for feedback
FEEDBACK_FILE = "feedback_data.json"

# 3. Utility Functions
def load_feedback():
    """Load feedback data from file or return empty list if file doesn't exist"""
    try:
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_feedback(feedback_list):
    """Save feedback data to file"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback_list, f, indent=4)

def validate_feedback(data):
    """Validate feedback submission data"""
    required_fields = ['name', 'email', 'rating', 'comment']
    errors = {}
    
    # Check for required fields
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f"{field.capitalize()} is required"
    
    # Email format validation
    if 'email' in data and data['email'] and '@' not in data['email']:
        errors['email'] = "Invalid email format"
    
    # Rating validation (1-5)
    if 'rating' in data:
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                errors['rating'] = "Rating must be between 1 and 5"
        except (ValueError, TypeError):
            errors['rating'] = "Rating must be a number between 1 and 5"
    
    return errors

def error_response(message, status_code):
    """Return standardized error response"""
    return jsonify({"success": False, "errors": message}), status_code

# Simple API key authentication for admin routes
API_KEY = os.getenv('API_KEY', 'admin_secret_key')  # In production, use env var

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        return error_response("Unauthorized", 401)
    return decorated_function

# 4. API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "time": datetime.now().isoformat()})

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Endpoint to submit new feedback"""
    try:
        data = request.json
        validation_errors = validate_feedback(data)
        
        if validation_errors:
            return error_response(validation_errors, 400)
        
        feedback_list = load_feedback()
        
        # Create new feedback entry
        new_feedback = {
            "id": str(uuid.uuid4()),
            "name": data['name'],
            "email": data['email'],
            "rating": int(data['rating']),
            "comment": data['comment'],
            "category": data.get('category', 'General'),
            "timestamp": datetime.now().isoformat(),
        }
        
        feedback_list.append(new_feedback)
        save_feedback(feedback_list)
        
        return jsonify({
            "success": True,
            "message": "Feedback submitted successfully",
            "feedback_id": new_feedback["id"]
        })
        
    except Exception as e:
        app.logger.error(f"Error submitting feedback: {str(e)}")
        return error_response("An unexpected error occurred", 500)

@app.route('/api/feedback', methods=['GET'])
@require_api_key
def get_all_feedback():
    """Endpoint to retrieve all feedback (admin only)"""
    try:
        feedback_list = load_feedback()
        return jsonify({
            "success": True,
            "count": len(feedback_list),
            "feedback": feedback_list
        })
    except Exception as e:
        app.logger.error(f"Error retrieving feedback: {str(e)}")
        return error_response("An unexpected error occurred", 500)

@app.route('/api/feedback/stats', methods=['GET'])
def get_feedback_stats():
    """Public endpoint to get feedback statistics"""
    try:
        feedback_list = load_feedback()
        
        if not feedback_list:
            return jsonify({
                "success": True,
                "stats": {
                    "count": 0,
                    "avg_rating": 0,
                    "categories": {}
                }
            })
        
        # Calculate stats
        total_rating = sum(item['rating'] for item in feedback_list)
        avg_rating = round(total_rating / len(feedback_list), 1)
        
        # Count by category
        categories = {}
        for item in feedback_list:
            cat = item.get('category', 'General')
            if cat in categories:
                categories[cat] += 1
            else:
                categories[cat] = 1
        
        return jsonify({
            "success": True,
            "stats": {
                "count": len(feedback_list),
                "avg_rating": avg_rating,
                "categories": categories
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving feedback stats: {str(e)}")
        return error_response("An unexpected error occurred", 500)

@app.route('/api/feedback/<feedback_id>', methods=['DELETE'])
@require_api_key
def delete_feedback(feedback_id):
    """Endpoint to delete specific feedback (admin only)"""
    try:
        feedback_list = load_feedback()
        
        # Find and remove the feedback with given ID
        new_list = [f for f in feedback_list if f['id'] != feedback_id]
        
        if len(new_list) == len(feedback_list):
            return error_response("Feedback not found", 404)
        
        save_feedback(new_list)
        
        return jsonify({
            "success": True,
            "message": "Feedback deleted successfully"
        })
        
    except Exception as e:
        app.logger.error(f"Error deleting feedback: {str(e)}")
        return error_response("An unexpected error occurred", 500)

# 5. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return error_response("Endpoint not found", 404)

@app.errorhandler(500)
def server_error(error):
    return error_response("Internal server error", 500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5325')), debug=True)