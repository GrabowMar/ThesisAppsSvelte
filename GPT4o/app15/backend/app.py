from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# In-memory data for simplicity; replace with a database for production.
kanban_board = {
    "columns": [
        {
            "id": 1,
            "name": "To Do",
            "tasks": [
                {"id": 1, "title": "Add Flask backend", "description": "Set up Flask backend for the Kanban app."},
                {"id": 2, "title": "Frontend Setup", "description": "Create React-based UI for Kanban."}
            ]
        },
        {
            "id": 2,
            "name": "In Progress",
            "tasks": []
        },
        {
            "id": 3,
            "name": "Done",
            "tasks": []
        }
    ]
}

@app.route('/api/board', methods=['GET'])
def get_board():
    # Returns full board data
    return jsonify(kanban_board), 200

@app.route('/api/task', methods=['POST'])
def add_task():
    # Add new task to a column
    task_data = request.json
    column_id = task_data.get('column_id')
    title = task_data.get('title')
    description = task_data.get('description')

    if not (column_id and title):
        return jsonify({"error": "Invalid data"}), 400

    # Find the column by ID
    for column in kanban_board["columns"]:
        if column["id"] == column_id:
            new_task = {
                "id": len(column["tasks"]) + 1,
                "title": title,
                "description": description
            }
            column["tasks"].append(new_task)
            return jsonify(new_task), 201

    return jsonify({"error": "Column not found"}), 404

@app.route('/api/task/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    # Update task details
    task_data = request.json
    new_title = task_data.get('title')
    new_description = task_data.get('description')

    for column in kanban_board["columns"]:
        for task in column["tasks"]:
            if task["id"] == task_id:
                if new_title:
                    task["title"] = new_title
                if new_description:
                    task["description"] = new_description
                return jsonify(task), 200

    return jsonify({"error": "Task not found"}), 404

@app.route('/api/task/<int:task_id>/move', methods=['PATCH'])
def move_task(task_id):
    # Move task between columns
    data = request.json
    target_column_id = data.get('target_column_id')

    if not target_column_id:
        return jsonify({"error": "No target column specified"}), 400

    task_to_move = None
    source_column = None

    for column in kanban_board["columns"]:
        for task in column["tasks"]:
            if task["id"] == task_id:
                task_to_move = task
                source_column = column
                break
        if task_to_move:
            break

    if not task_to_move:
        return jsonify({"error": "Task not found"}), 404

    for column in kanban_board["columns"]:
        if column["id"] == target_column_id:
            source_column["tasks"].remove(task_to_move)
            column["tasks"].append(task_to_move)
            return jsonify({"message": "Task moved successfully"}), 200

    return jsonify({"error": "Target column not found"}), 404

@app.route('/api/task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    # Delete a task from a column
    for column in kanban_board["columns"]:
        for task in column["tasks"]:
            if task["id"] == task_id:
                column["tasks"].remove(task)
                return jsonify({"message": "Task deleted"}), 200

    return jsonify({"error": "Task not found"}), 404

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 5269))
    app.run(host='0.0.0.0', port=PORT)
