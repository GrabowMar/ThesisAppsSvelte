import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [boards, setBoards] = useState([]);
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetch('/api/boards')
      .then(response => response.json())
      .then(data => setBoards(data));

    fetch('/api/tasks')
      .then(response => response.json())
      .then(data => setTasks(data));
  }, []);

  const createBoard = async (board) => {
    const response = await fetch('/api/boards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(board),
    });
    const newBoard = await response.json();
    setBoards([...boards, newBoard]);
  };

  const createTask = async (task) => {
    const response = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(task),
    });
    const newTask = await response.json();
    setTasks([...tasks, newTask]);
  };

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/boards">Boards</Link>
        <Link to="/tasks">Tasks</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/boards" element={<Boards boards={boards} createBoard={createBoard} />} />
        <Route path="/tasks" element={<Tasks tasks={tasks} createTask={createTask} />} />
      </Routes>
    </Router>
  );
};

const Home = () => <h1>Welcome to Kanban System</h1>;

const Boards = ({ boards, createBoard }) => {
  const [boardName, setBoardName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    createBoard({ name: boardName });
    setBoardName('');
  };

  return (
    <div>
      <h1>Boards</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={boardName}
          onChange={(e) => setBoardName(e.target.value)}
          placeholder="Board Name"
        />
        <button type="submit">Create Board</button>
      </form>
      <ul>
        {boards.map(board => (
          <li key={board.id}>{board.name}</li>
        ))}
      </ul>
    </div>
  );
};

const Tasks = ({ tasks, createTask }) => {
  const [taskName, setTaskName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    createTask({ name: taskName });
    setTaskName('');
  };

  return (
    <div>
      <h1>Tasks</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={taskName}
          onChange={(e) => setTaskName(e.target.value)}
          placeholder="Task Name"
        />
        <button type="submit">Create Task</button>
      </form>
      <ul>
        {tasks.map(task => (
          <li key={task.id}>{task.name}</li>
        ))}
      </ul>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
