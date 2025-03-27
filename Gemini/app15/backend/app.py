from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Sample Data (Replace with a Database in a real application)
boards = {
    "board1": {
        "name": "Project Board",
        "columns": {
            "column1": {"name": "To Do", "tasks": [{"id": "task1", "title": "Implement Feature A", "description": "Details of Feature A"}, {"id": "task2", "title": "Design UI", "description": "UI Mockups"}]},
            "column2": {"name": "In Progress", "tasks": [{"id": "task3", "title": "Develop API", "description": "API Endpoints"},]},
            "column3": {"name": "Done", "tasks": [{"id": "task4", "title": "Write Tests", "description": "Unit & Integration Tests"}]}
        }
    }
}

# Helper Functions
def find_task(board_id, column_id, task_id):
    """Finds a task within a board and column."""
    board = boards.get(board_id)
    if not board:
        return None, "Board not found", 404

    column = board["columns"].get(column_id)
    if not column:
        return None, "Column not found", 404

    for task in column["tasks"]:
        if task["id"] == task_id:
            return task, None, 200
    return None, "Task not found", 404

# API Routes

@app.route('/api/boards', methods=['GET'])
def get_boards():
    """Returns a list of board names."""
    board_list = [{"id": board_id, "name": board["name"]} for board_id, board in boards.items()]
    return jsonify(board_list)

@app.route('/api/boards/<board_id>', methods=['GET'])
def get_board(board_id):
    """Returns the specified board."""
    board = boards.get(board_id)
    if board:
        return jsonify(board)
    else:
        return jsonify({"message": "Board not found"}), 404

@app.route('/api/boards/<board_id>/columns', methods=['POST'])
def create_column(board_id):
    """Creates a new column in the specified board."""
    board = boards.get(board_id)
    if not board:
        return jsonify({"message": "Board not found"}), 404

    data = request.get_json()
    column_name = data.get("name")
    if not column_name:
        return jsonify({"message": "Column name is required"}), 400

    new_column_id = f"column{len(board['columns']) + 1}"  # Simple ID generation
    board["columns"][new_column_id] = {"name": column_name, "tasks": []}

    return jsonify({"id": new_column_id, "name": column_name}), 201

@app.route('/api/boards/<board_id>/columns/<column_id>/tasks', methods=['POST'])
def create_task(board_id, column_id):
    """Creates a new task in the specified column."""
    board = boards.get(board_id)
    if not board:
        return jsonify({"message": "Board not found"}), 404

    column = board["columns"].get(column_id)
    if not column:
        return jsonify({"message": "Column not found"}), 404

    data = request.get_json()
    task_title = data.get("title")
    task_description = data.get("description", "")

    if not task_title:
        return jsonify({"message": "Task title is required"}), 400

    new_task_id = f"task{len(column['tasks']) + 1}"  # Simple ID generation
    new_task = {"id": new_task_id, "title": task_title, "description": task_description}
    column["tasks"].append(new_task)

    return jsonify(new_task), 201

@app.route('/api/boards/<board_id>/columns/<column_id>/tasks/<task_id>', methods=['PUT'])
def update_task(board_id, column_id, task_id):
    """Updates an existing task."""
    task, error, status_code = find_task(board_id, column_id, task_id)
    if error:
        return jsonify({"message": error}), status_code

    data = request.get_json()
    task["title"] = data.get("title", task["title"])
    task["description"] = data.get("description", task["description"])

    return jsonify(task), 200

@app.route('/api/boards/<board_id>/columns/<column_id>/tasks/<task_id>', methods=['DELETE'])
def delete_task(board_id, column_id, task_id):
    """Deletes a task."""
    board = boards.get(board_id)
    if not board:
        return jsonify({"message": "Board not found"}), 404

    column = board["columns"].get(column_id)
    if not column:
        return jsonify({"message": "Column not found"}), 404

    original_task_count = len(column["tasks"])
    column["tasks"] = [task for task in column["tasks"] if task["id"] != task_id]
    if len(column["tasks"]) == original_task_count:
        return jsonify({"message": "Task not found"}), 404

    return jsonify({"message": "Task deleted"}), 200

@app.route('/api/move_task', methods=['POST'])
def move_task():
     """Moves a task from one column to another."""
     data = request.get_json()
     source_board_id = data.get("source_board_id")
     source_column_id = data.get("source_column_id")
     task_id = data.get("task_id")
     dest_board_id = data.get("dest_board_id")
     dest_column_id = data.get("dest_column_id")

     source_board = boards.get(source_board_id)
     dest_board = boards.get(dest_board_id)
     if not source_board or not dest_board:
        return jsonify({"message": "Board not found"}), 404

     source_column = source_board["columns"].get(source_column_id)
     dest_column = dest_board["columns"].get(dest_column_id)
     if not source_column or not dest_column:
        return jsonify({"message": "Column not found"}), 404

     # Find the task in the source column
     task_to_move = None
     for task in source_column["tasks"]:
        if task["id"] == task_id:
            task_to_move = task
            break

     if not task_to_move:
        return jsonify({"message": "Task not found in source column"}), 404

     # Remove the task from the source column
     source_column["tasks"] = [task for task in source_column["tasks"] if task["id"] != task_id]

     # Add the task to the destination column
     dest_column["tasks"].append(task_to_move)

     return jsonify({"message": "Task moved successfully"}), 200

# Example Error Handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({"message": "Resource not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5429')), debug=True)
