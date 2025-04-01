from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from uuid import uuid4
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory database simulation
boards = {
    'default': {
        'id': 'default',
        'columns': [
            {'id': 'todo', 'title': 'To Do', 'taskIds': []},
            {'id': 'progress', 'title': 'In Progress', 'taskIds': []},
            {'id': 'done', 'title': 'Done', 'taskIds': []}
        ],
        'tasks': {}
    }
}

# Utility functions
def get_board(board_id):
    board = boards.get(board_id)
    if not board:
        abort(404, description="Board not found")
    return board

# API Routes
@app.route('/api/boards/<board_id>', methods=['GET'])
def get_board_data(board_id):
    board = get_board(board_id)
    return jsonify(board)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    task_id = str(uuid4())
    board = get_board('default')
    
    new_task = {
        'id': task_id,
        'title': data['title'],
        'description': data.get('description', ''),
        'column': 'todo'
    }
    
    board['tasks'][task_id] = new_task
    board['columns'][0]['taskIds'].append(task_id)
    return jsonify(new_task), 201

@app.route('/api/tasks/<task_id>/move', methods=['PATCH'])
def move_task(task_id):
    data = request.get_json()
    board = get_board('default')
    
    if task_id not in board['tasks']:
        abort(404, description="Task not found")
        
    # Remove from old column
    old_column_id = board['tasks'][task_id]['column']
    old_column = next(c for c in board['columns'] if c['id'] == old_column_id)
    old_column['taskIds'].remove(task_id)
    
    # Add to new column
    new_column_id = data['newColumnId']
    new_column = next(c for c in board['columns'] if c['id'] == new_column_id)
    new_column['taskIds'].insert(data['newIndex'], task_id)
    board['tasks'][task_id]['column'] = new_column_id
    
    return jsonify({'status': 'success'})

# Error handlers
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=str(e)), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5589')))
