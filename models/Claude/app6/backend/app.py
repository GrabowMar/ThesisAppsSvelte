# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import uuid
from datetime import datetime
import json
from werkzeug.exceptions import NotFound, BadRequest

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. Database (In-memory for simplicity - would use SQLAlchemy in production)
# Data structure: notes.json file to persist data
DATA_FILE = 'notes.json'

def initialize_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({
                "notes": [],
                "categories": ["Work", "Personal", "Ideas", "To-Do"]
            }, f)

def read_db():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_db()
        return {"notes": [], "categories": ["Work", "Personal", "Ideas", "To-Do"]}

def write_db(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# 4. Utility Functions
def get_timestamp():
    return datetime.now().isoformat()

# 5. API Routes

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Notes API is running"})

# Get all notes
@app.route('/api/notes', methods=['GET'])
def get_notes():
    search_term = request.args.get('search', '').lower()
    category_filter = request.args.get('category', '')
    archived = request.args.get('archived') == 'true'
    
    db = read_db()
    notes = db["notes"]
    
    # Apply filters
    if search_term:
        notes = [note for note in notes if search_term in note['title'].lower() 
                 or search_term in note['content'].lower()]
    
    if category_filter:
        notes = [note for note in notes if category_filter == note['category']]
    
    notes = [note for note in notes if note['archived'] == archived]
    
    # Sort by last modified date (newest first)
    notes.sort(key=lambda x: x['updated_at'], reverse=True)
    
    return jsonify(notes)

# Get a specific note
@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    db = read_db()
    for note in db["notes"]:
        if note['id'] == note_id:
            return jsonify(note)
    
    abort(404, description=f"Note with id {note_id} not found")

# Create a new note
@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    
    if not data or 'title' not in data or 'content' not in data:
        abort(400, description="Missing required note data (title and content are required)")
    
    now = get_timestamp()
    new_note = {
        'id': str(uuid.uuid4()),
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', ''),
        'archived': False,
        'created_at': now,
        'updated_at': now
    }
    
    db = read_db()
    db["notes"].append(new_note)
    write_db(db)
    
    return jsonify(new_note), 201

# Update a note
@app.route('/api/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    
    if not data:
        abort(400, description="Missing note data")
    
    db = read_db()
    for i, note in enumerate(db["notes"]):
        if note['id'] == note_id:
            # Update allowed fields
            if 'title' in data:
                note['title'] = data['title']
            if 'content' in data:
                note['content'] = data['content']
            if 'category' in data:
                note['category'] = data['category']
            if 'archived' in data:
                note['archived'] = data['archived']
            
            note['updated_at'] = get_timestamp()
            db["notes"][i] = note
            write_db(db)
            return jsonify(note)
    
    abort(404, description=f"Note with id {note_id} not found")

# Delete a note
@app.route('/api/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    db = read_db()
    
    for i, note in enumerate(db["notes"]):
        if note['id'] == note_id:
            deleted_note = db["notes"].pop(i)
            write_db(db)
            return jsonify(deleted_note)
    
    abort(404, description=f"Note with id {note_id} not found")

# Get all categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    db = read_db()
    return jsonify(db["categories"])

# Create a category
@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    
    if not data or 'name' not in data:
        abort(400, description="Missing required category name")
    
    db = read_db()
    if data['name'] not in db["categories"]:
        db["categories"].append(data['name'])
        write_db(db)
    
    return jsonify(db["categories"])

# 6. Error Handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": str(error.description)}), 404

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({"error": str(error.description)}), 400

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Initialize database on startup
initialize_db()

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5331')), debug=True)
