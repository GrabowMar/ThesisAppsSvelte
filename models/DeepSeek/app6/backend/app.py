# 1. Imports Section
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import os
import uuid

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# 3. In-memory database for demo purposes (replace with a proper database in production)
notes_db = []

# 4. Utility Functions
def find_note(note_id):
    for note in notes_db:
        if note['id'] == note_id:
            return note
    return None

# 5. API Routes

# Create a note
@app.route('/api/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        abort(400, description="Title and content are required.")
    
    new_note = {
        'id': str(uuid.uuid4()),
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', 'Uncategorized'),
        'archived': False
    }
    notes_db.append(new_note)
    return jsonify(new_note), 201

# List all notes
@app.route('/api/notes', methods=['GET'])
def list_notes():
    return jsonify(notes_db)

# Get a single note
@app.route('/api/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    note = find_note(note_id)
    if not note:
        abort(404, description="Note not found.")
    return jsonify(note)

# Update a note
@app.route('/api/notes/<note_id>', methods=['PUT'])
def update_note(note_id):
    note = find_note(note_id)
    if not note:
        abort(404, description="Note not found.")
    
    data = request.get_json()
    if 'title' in data:
        note['title'] = data['title']
    if 'content' in data:
        note['content'] = data['content']
    if 'category' in data:
        note['category'] = data['category']
    
    return jsonify(note)

# Archive a note
@app.route('/api/notes/<note_id>/archive', methods=['PUT'])
def archive_note(note_id):
    note = find_note(note_id)
    if not note:
        abort(404, description="Note not found.")
    
    note['archived'] = True
    return jsonify(note)

# Search notes by title or category
@app.route('/api/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q', '').lower()
    results = [note for note in notes_db if query in note['title'].lower() or query in note['category'].lower()]
    return jsonify(results)

# 6. Error Handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": str(error)}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5171')))
