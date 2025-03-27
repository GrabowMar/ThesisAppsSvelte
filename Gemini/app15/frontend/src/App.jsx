import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [boards, setBoards] = useState([]);
    const [selectedBoardId, setSelectedBoardId] = useState(null);
    const [board, setBoard] = useState(null);
    const [newColumnName, setNewColumnName] = useState('');
    const [newTaskTitle, setNewTaskTitle] = useState('');
    const [newTaskDescription, setNewTaskDescription] = useState('');

    useEffect(() => {
        fetchBoards();
    }, []);

    useEffect(() => {
        if (selectedBoardId) {
            fetchBoard(selectedBoardId);
        }
    }, [selectedBoardId]);

    const fetchBoards = async () => {
        try {
            const response = await fetch('/api/boards');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            setBoards(data);
        } catch (error) {
            console.error("Failed to fetch boards:", error);
        }
    };

    const fetchBoard = async (boardId) => {
        try {
            const response = await fetch(`/api/boards/${boardId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            const data = await response.json();
            setBoard(data);
        } catch (error) {
            console.error("Failed to fetch board:", error);
        }
    };

    const handleBoardSelect = (boardId) => {
        setSelectedBoardId(boardId);
    };

    const handleCreateColumn = async () => {
        if (!newColumnName) return;
        try {
            const response = await fetch(`/api/boards/${selectedBoardId}/columns`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newColumnName }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            setNewColumnName('');
            fetchBoard(selectedBoardId); // Refresh board data
        } catch (error) {
            console.error("Failed to create column:", error);
        }
    };

    const handleCreateTask = async (columnId) => {
        if (!newTaskTitle) return;
        try {
            const response = await fetch(`/api/boards/${selectedBoardId}/columns/${columnId}/tasks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ title: newTaskTitle, description: newTaskDescription }),
            });
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            setNewTaskTitle('');
            setNewTaskDescription('');
            fetchBoard(selectedBoardId); // Refresh board data
        } catch (error) {
            console.error("Failed to create task:", error);
        }
    };

    const handleMoveTask = async (taskId, sourceColumnId, destColumnId) => {
        try {
            const response = await fetch('/api/move_task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_board_id: selectedBoardId,
                    source_column_id: sourceColumnId,
                    task_id: taskId,
                    dest_board_id: selectedBoardId,
                    dest_column_id: destColumnId,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            fetchBoard(selectedBoardId); // Refresh board data
        } catch (error) {
            console.error('Failed to move task:', error);
        }
    };

    const handleDragStart = (e, taskId, columnId) => {
      e.dataTransfer.setData("taskId", taskId);
      e.dataTransfer.setData("sourceColumnId", columnId);
    };

    const handleDrop = (e, destColumnId) => {
        e.preventDefault();
        const taskId = e.dataTransfer.getData("taskId");
        const sourceColumnId = e.dataTransfer.getData("sourceColumnId");
        handleMoveTask(taskId, sourceColumnId, destColumnId);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
    };

    if (!selectedBoardId) {
        return (
            <div className="board-selection">
                <h1>Select a Board</h1>
                <ul>
                    {boards.map(board => (
                        <li key={board.id} onClick={() => handleBoardSelect(board.id)}>{board.name}</li>
                    ))}
                </ul>
            </div>
        );
    }

    if (!board) {
        return <div>Loading board...</div>;
    }

    return (
        <div className="kanban-board">
            <h1>{board.name}</h1>

            <div className="column-container">
                {Object.entries(board.columns).map(([columnId, column]) => (
                    <div
                        key={columnId}
                        className="kanban-column"
                        onDrop={(e) => handleDrop(e, columnId)}
                        onDragOver={handleDragOver}
                    >
                        <h2>{column.name}</h2>
                        {column.tasks.map(task => (
                            <div
                                key={task.id}
                                className="kanban-task"
                                draggable
                                onDragStart={(e) => handleDragStart(e, task.id, columnId)}
                            >
                                <h3>{task.title}</h3>
                                <p>{task.description}</p>
                            </div>
                        ))}
                        <div className="new-task-form">
                            <input
                                type="text"
                                placeholder="New Task Title"
                                value={newTaskTitle}
                                onChange={(e) => setNewTaskTitle(e.target.value)}
                            />
                            <textarea
                                placeholder="New Task Description"
                                value={newTaskDescription}
                                onChange={(e) => setNewTaskDescription(e.target.value)}
                            />
                            <button onClick={() => handleCreateTask(columnId)}>Add Task</button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="new-column-form">
                <input
                    type="text"
                    placeholder="New Column Name"
                    value={newColumnName}
                    onChange={(e) => setNewColumnName(e.target.value)}
                />
                <button onClick={handleCreateColumn}>Add Column</button>
            </div>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
