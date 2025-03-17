# app.py

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample in-memory data storage
boards = [
    {"id": 1, "name": "Board 1", "columns": [
        {"id": 1, "name": "To-Do", "tasks": [
            {"id": 1, "name": "Task 1", "description": "Task 1 description"},
            {"id": 2, "name": "Task 2", "description": "Task 2 description"}
        ]},
        {"id": 2, "name": "In Progress", "tasks": [
            {"id": 3, "name": "Task 3", "description": "Task 3 description"},
            {"id": 4, "name": "Task 4", "description": "Task 4 description"}
        ]},
        {"id": 3, "name": "Done", "tasks": [
            {"id": 5, "name": "Task 5", "description": "Task 5 description"},
            {"id": 6, "name": "Task 6", "description": "Task 6 description"}
        ]}
    ]}
]

# Route to get all boards
@app.route('/boards', methods=['GET'])
def get_boards():
    return jsonify(boards)

# Route to get a specific board
@app.route('/boards/<int:board_id>', methods=['GET'])
def get_board(board_id):
    for board in boards:
        if board['id'] == board_id:
            return jsonify(board)
    return jsonify({"error": "Board not found"})

# Route to create a new board
@app.route('/boards', methods=['POST'])
def create_board():
    new_board = {
        "id": len(boards) + 1,
        "name": request.json['name'],
        "columns": []
    }
    boards.append(new_board)
    return jsonify(new_board)

# Route to update a board
@app.route('/boards/<int:board_id>', methods=['PUT'])
def update_board(board_id):
    for board in boards:
        if board['id'] == board_id:
            board['name'] = request.json.get('name', board['name'])
            return jsonify(board)
    return jsonify({"error": "Board not found"})

# Route to delete a board
@app.route('/boards/<int:board_id>', methods=['DELETE'])
def delete_board(board_id):
    for board in boards:
        if board['id'] == board_id:
            boards.remove(board)
            return jsonify({"message": "Board deleted"})
    return jsonify({"error": "Board not found"})

# Route to get all columns for a board
@app.route('/boards/<int:board_id>/columns', methods=['GET'])
def get_columns(board_id):
    for board in boards:
        if board['id'] == board_id:
            return jsonify(board['columns'])
    return jsonify({"error": "Board not found"})

# Route to create a new column
@app.route('/boards/<int:board_id>/columns', methods=['POST'])
def create_column(board_id):
    for board in boards:
        if board['id'] == board_id:
            new_column = {
                "id": len(board['columns']) + 1,
                "name": request.json['name'],
                "tasks": []
            }
            board['columns'].append(new_column)
            return jsonify(new_column)
    return jsonify({"error": "Board not found"})

# Route to update a column
@app.route('/boards/<int:board_id>/columns/<int:column_id>', methods=['PUT'])
def update_column(board_id, column_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    column['name'] = request.json.get('name', column['name'])
                    return jsonify(column)
    return jsonify({"error": "Column not found"})

# Route to delete a column
@app.route('/boards/<int:board_id>/columns/<int:column_id>', methods=['DELETE'])
def delete_column(board_id, column_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    board['columns'].remove(column)
                    return jsonify({"message": "Column deleted"})
    return jsonify({"error": "Column not found"})

# Route to get all tasks for a column
@app.route('/boards/<int:board_id>/columns/<int:column_id>/tasks', methods=['GET'])
def get_tasks(board_id, column_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    return jsonify(column['tasks'])
    return jsonify({"error": "Column not found"})

# Route to create a new task
@app.route('/boards/<int:board_id>/columns/<int:column_id>/tasks', methods=['POST'])
def create_task(board_id, column_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    new_task = {
                        "id": len(column['tasks']) + 1,
                        "name": request.json['name'],
                        "description": request.json['description']
                    }
                    column['tasks'].append(new_task)
                    return jsonify(new_task)
    return jsonify({"error": "Column not found"})

# Route to update a task
@app.route('/boards/<int:board_id>/columns/<int:column_id>/tasks/<int:task_id>', methods=['PUT'])
def update_task(board_id, column_id, task_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    for task in column['tasks']:
                        if task['id'] == task_id:
                            task['name'] = request.json.get('name', task['name'])
                            task['description'] = request.json.get('description', task['description'])
                            return jsonify(task)
    return jsonify({"error": "Task not found"})

# Route to delete a task
@app.route('/boards/<int:board_id>/columns/<int:column_id>/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(board_id, column_id, task_id):
    for board in boards:
        if board['id'] == board_id:
            for column in board['columns']:
                if column['id'] == column_id:
                    for task in column['tasks']:
                        if task['id'] == task_id:
                            column['tasks'].remove(task)
                            return jsonify({"message": "Task deleted"})
    return jsonify({"error": "Task not found"})

if __name__ == '__main__':
    app.run(port=5029)
