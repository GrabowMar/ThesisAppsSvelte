import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const API_URL = 'http://localhost:5189/api';

function App() {
    const [boards, setBoards] = useState([]);
    const [selectedBoard, setSelectedBoard] = useState(null);
    const [tasks, setTasks] = useState({});

    // Fetch boards on mount
    useEffect(() => {
        fetch(`${API_URL}/boards`)
            .then((res) => res.json())
            .then(setBoards);
    }, []);

    // Handle board selection
    const handleBoardSelect = (boardId) => {
        const board = boards.find((b) => b.id === boardId);
        setSelectedBoard(board);
    };

    // Handle task creation
    const handleCreateTask = (columnId, taskData) => {
        fetch(`${API_URL}/columns/${columnId}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData),
        })
            .then((res) => res.json())
            .then((task) => {
                setTasks((prev) => ({
                    ...prev,
                    [task.id]: task,
                }));
            });
    };

    // Render UI
    return (
        <main>
            <h1>Kanban Board</h1>
            <div className="board-list">
                {boards.map((board) => (
                    <button key={board.id} onClick={() => handleBoardSelect(board.id)}>
                        {board.name}
                    </button>
                ))}
            </div>
            {selectedBoard && (
                <div className="board">
                    <h2>{selectedBoard.name}</h2>
                    <div className="columns">
                        {selectedBoard.columns.map((columnId) => (
                            <Column
                                key={columnId}
                                columnId={columnId}
                                tasks={tasks}
                                onCreateTask={handleCreateTask}
                            />
                        ))}
                    </div>
                </div>
            )}
        </main>
    );
}

function Column({ columnId, tasks, onCreateTask }) {
    const columnTasks = Object.values(tasks).filter((task) => task.status === columnId);

    const handleTaskCreate = () => {
        const title = prompt('Enter task title:');
        const description = prompt('Enter task description:');
        if (title && description) {
            onCreateTask(columnId, { title, description });
        }
    };

    return (
        <div className="column">
            <div className="column-header">
                <h3>Column {columnId}</h3>
                <button onClick={handleTaskCreate}>+ Add Task</button>
            </div>
            <div className="tasks">
                {columnTasks.map((task) => (
                    <Task key={task.id} task={task} />
                ))}
            </div>
        </div>
    );
}

function Task({ task }) {
    return (
        <div className="task">
            <h4>{task.title}</h4>
            <p>{task.description}</p>
        </div>
    );
}

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
