# app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# In-memory data store (replace this with a proper DB in production)
notes = []
archived_notes = []

# Helper function for generating unique note IDs
def generate_id():
    if len(notes) == 0 and len(archived_notes) == 0:
        return 1
    all_notes = notes + archived_notes
    max_id = max(note['id'] for note in all_notes)
    return max_id + 1

# ROUTES
@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get all active notes."""
    return jsonify({"notes": notes}), 200

@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note."""
    data = request.get_json()
    if not data.get("title") or not data.get("content"):
        return jsonify({"error": "Title and content are required!"}), 400

    new_note = {
        "id": generate_id(),
        "title": data['title'],
        "content": data['content'],
        "category": data.get('category', 'Uncategorized'),
        "archived": False
    }
    notes.append(new_note)
    return jsonify({"message": "Note created successfully!", "note": new_note}), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Edit a note by ID."""
    data = request.get_json()
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return jsonify({"error": "Note not found!"}), 404

    note.update({
        "title": data.get("title", note['title']),
        "content": data.get("content", note['content']),
        "category": data.get("category", note['category']),
    })
    return jsonify({"message": "Note updated successfully!", "note": note}), 200

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note by ID."""
    global notes
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return jsonify({"error": "Note not found!"}), 404

    notes = [n for n in notes if n['id'] != note_id]
    return jsonify({"message": "Note deleted successfully!"}), 200

@app.route('/api/notes/archive/<int:note_id>', methods=['PUT'])
def archive_note(note_id):
    """Archive a note."""
    global notes, archived_notes
    note = next((n for n in notes if n['id'] == note_id), None)
    if not note:
        return jsonify({"error": "Note not found!"}), 404

    notes = [n for n in notes if n['id'] != note_id]
    note['archived'] = True
    archived_notes.append(note)
    return jsonify({"message": "Note archived successfully!", "note": note}), 200

@app.route('/api/search', methods=['GET'])
def search_notes():
    """Search notes by term."""
    query = request.args.get('q', '').lower()
    matching_notes = [n for n in notes if query in n['title'].lower() or query in n['content'].lower()]
    return jsonify({"matching_notes": matching_notes}), 200

# Main entry point
PORT = int(os.getenv('PORT', 5251))
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=PORT)
