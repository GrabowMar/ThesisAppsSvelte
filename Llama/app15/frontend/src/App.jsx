// App.jsx
import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
    const [boards, setBoards] = useState([]);
    const [currentBoard, setCurrentBoard] = useState({});
    const [currentColumn, setCurrentColumn] = useState({});
    const [tasks, setTasks] = useState([]);

    useEffect(() => {
        fetch('http://localhost:5029/boards')
            .then(response => response.json())
            .then(data => setBoards(data));
    }, []);

    const handleBoardClick = (board) => {
        setCurrentBoard(board);
        fetch(`http://localhost:5029/boards/${board.id}/columns`)
            .then(response => response.json())
            .then(data => {
                setCurrentColumn(data[0]);
                fetch(`http://localhost:5029/boards/${board.id}/columns/${data[0].id}/tasks`)
                    .then(response => response.json())
                    .then(data => setTasks(data));
            });
    };

    const handleColumnClick = (column) => {
        setCurrentColumn(column);
        fetch(`http://localhost:5029/boards/${currentBoard.id}/columns/${column.id}/tasks`)
            .then(response => response.json())
            .then(data => setTasks(data));
    };

    const handleTaskClick = (task) => {
        console.log(task);
    };

    const handleCreateTask = () => {
        const newTask = {
            name: 'New Task',
            description: 'New Task Description'
        };
        fetch(`http://localhost:5029/boards/${currentBoard.id}/columns/${currentColumn.id}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newTask)
        })
            .then(response => response.json())
            .then(data => setTasks([...tasks, data]));
    };

    return (
        <div className="App">
            <h1>Kanban Board</h1>
            <div className="boards">
                {boards.map(board => (
                    <div key={board.id} className="board" onClick={() => handleBoardClick(board)}>
                        {board.name}
                    </div>
                ))}
            </div>
            {currentBoard.id && (
                <div className="columns">
                    {currentBoard.columns.map(column => (
                        <div key={column.id} className="column" onClick={() => handleColumnClick(column)}>
                            {column.name}
                        </div>
                    ))}
                </div>
            )}
            {currentColumn.id && (
                <div className="tasks">
                    {tasks.map(task => (
                        <div key={task.id} className="task" onClick={() => handleTaskClick(task)}>
                            {task.name}
                        </div>
                    ))}
                    <button className="create-task-button" onClick={handleCreateTask}>
                        Create Task
                    </button>
                </div>
            )}
        </div>
    );
}

export default App;
