from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory database for simplicity
boards = {}

@app.route('/')
def home():
    return "Kanban Board API"

@app.route('/boards', methods=['POST'])
def create_board():
    data = request.json
    board_id = data.get('id')
    board_name = data.get('name')
    if not board_id or not board_name:
        return jsonify({'error': 'Board ID and name are required'}), 400
    boards[board_id] = {
        'name': board_name,
        'columns': {}
    }
    return jsonify({'message': 'Board created successfully'}), 201

@app.route('/boards/<board_id>', methods=['GET'])
def get_board(board_id):
    board = boards.get(board_id)
    if not board:
        return jsonify({'error': 'Board not found'}), 404
    return jsonify(board), 200

@app.route('/boards/<board_id>/columns', methods=['POST'])
def create_column(board_id):
    data = request.json
    column_id = data.get('id')
    column_name = data.get('name')
    if not column_id or not column_name:
        return jsonify({'error': 'Column ID and name are required'}), 400
    if board_id not in boards:
        return jsonify({'error': 'Board not found'}), 404
    boards[board_id]['columns'][column_id] = {
        'name': column_name,
        'tasks': []
    }
    return jsonify({'message': 'Column created successfully'}), 201

@app.route('/boards/<board_id>/columns/<column_id>/tasks', methods=['POST'])
def create_task(board_id, column_id):
    data = request.json
    task_id = data.get('id')
    task_name = data.get('name')
    if not task_id or not task_name:
        return jsonify({'error': 'Task ID and name are required'}), 400
    if board_id not in boards or column_id not in boards[board_id]['columns']:
        return jsonify({'error': 'Board or column not found'}), 404
    boards[board_id]['columns'][column_id]['tasks'].append({
        'id': task_id,
        'name': task_name
    })
    return jsonify({'message': 'Task created successfully'}), 201

@app.route('/boards/<board_id>/columns/<column_id>/tasks/<task_id>', methods=['PUT'])
def update_task(board_id, column_id, task_id):
    data = request.json
    task_name = data.get('name')
    if not task_name:
        return jsonify({'error': 'Task name is required'}), 400
    if board_id not in boards or column_id not in boards[board_id]['columns']:
        return jsonify({'error': 'Board or column not found'}), 404
    tasks = boards[board_id]['columns'][column_id]['tasks']
    for task in tasks:
        if task['id'] == task_id:
            task['name'] = task_name
            return jsonify({'message': 'Task updated successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

@app.route('/boards/<board_id>/columns/<column_id>/tasks/<task_id>', methods=['DELETE'])
def delete_task(board_id, column_id, task_id):
    if board_id not in boards or column_id not in boards[board_id]['columns']:
        return jsonify({'error': 'Board or column not found'}), 404
    tasks = boards[board_id]['columns'][column_id]['tasks']
    for task in tasks:
        if task['id'] == task_id:
            tasks.remove(task)
            return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    app.run(port=5349)
