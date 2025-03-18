from flask import Flask, jsonify, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# In-memory data store for notes
notes = []
next_note_id = 1

# Helper function to find a note by ID
def find_note(note_id):
    for note in notes:
        if note['id'] == note_id:
            return note
    return None

# Routes for note management
@app.route('/api/notes', methods=['GET'])
def get_notes():
    # Get all notes (excluding archived ones by default)
    unarchived_notes = [note for note in notes if not note.get('archived', False)]
    return jsonify(unarchived_notes)

@app.route('/api/notes/archived', methods=['GET'])
def get_archived_notes():
    # Get all archived notes
    archived_notes = [note for note in notes if note.get('archived', False)]
    return jsonify(archived_notes)

@app.route('/api/notes', methods=['POST'])
def create_note():
    global next_note_id
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        abort(400, description="Title and content are required.")
    
    new_note = {
        'id': next_note_id,
        'title': data['title'],
        'content': data['content'],
        'category': data.get('category', 'Uncategorized'),
        'archived': False
    }
    notes.append(new_note)
    next_note_id += 1
    return jsonify(new_note), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    note = find_note(note_id)
    if not note:
        abort(404, description="Note not found.")
    
    if 'title' in data:
        note['title'] = data['title']
    if 'content' in data:
        note['content'] = data['content']
    if 'category' in data:
        note['category'] = data['category']
    if 'archived' in data:
        note['archived'] = data['archived']
    
    return jsonify(note)

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = find_note(note_id)
    if not note:
        abort(404, description="Note not found.")
    
    notes.remove(note)
    return jsonify({'message': 'Note deleted successfully.'})

@app.route('/api/notes/search', methods=['GET'])
def search_notes():
    query = request.args.get('q')
    if not query:
        abort(400, description="Search query is required.")
    
    results = [note for note in notes if query.lower() in note['title'].lower() or query.lower() in note['content'].lower()]
    return jsonify(results)

if __name__ == '__main__':
    app.run(port=5171, debug=True)
