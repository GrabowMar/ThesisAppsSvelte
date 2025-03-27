from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import uuid
import os

app = Flask(__name__)
CORS(app)

# In-memory data storage for boards, tasks, and columns
boards = {}
tasks = {}
columns = {}

# Utility functions
def generate_id():
    return str(uuid.uuid4())

# API Routes
@app.route('/api/boards', methods=['GET'])
def get_boards():
    return jsonify(list(boards.values()))

@app.route('/api/boards', methods=['POST'])
def create_board():
    data = request.get_json()
    board_id = generate_id()
    board = {
        'id': board_id,
        'name': data['name'],
        'columns': []
    }
    boards[board_id] = board
    return jsonify(board), 201

@app.route('/api/boards/<board_id>/columns', methods=['POST'])
def create_column(board_id):
    if board_id not in boards:
        abort(404, description="Board not found")
    data = request.get_json()
    column_id = generate_id()
    column = {
        'id': column_id,
        'name': data['name'],
        'tasks': []
    }
    columns[column_id] = column
    boards[board_id]['columns'].append(column_id)
    return jsonify(column), 201

@app.route('/api/columns/<column_id>/tasks', methods=['POST'])
def create_task(column_id):
    if column_id not in columns:
        abort(404, description="Column not found")
    data = request.get_json()
    task_id = generate_id()
    task = {
        'id': task_id,
        'title': data['title'],
        'description': data['description'],
        'status': column_id
    }
    tasks[task_id] = task
    columns[column_id]['tasks'].append(task_id)
    return jsonify(task), 201

@app.route('/api/tasks/<task_id>', methods=['PUT'])
def update_task(task_id):
    if task_id not in tasks:
        abort(404, description="Task not found")
    data = request.get_json()
    tasks[task_id].update(data)
    return jsonify(tasks[task_id])

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if task_id not in tasks:
        abort(404, description="Task not found")
    del tasks[task_id]
    return '', 204

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5189')))
