import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Utility functions
const apiUrl = 'http://localhost:5509/api';
const token = localStorage.getItem('token');

const fetchData = async (endpoint, method = 'GET', body = null) => {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };

  try {
    const response = await fetch(`${apiUrl}${endpoint}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};

// Components
const Login = ({ setToken }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${apiUrl}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      localStorage.setItem('token', data.token);
      setToken(data.token);
    } catch (error) {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Login</button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
};

const BoardList = ({ boards, setCurrentBoard }) => {
  return (
    <div className="board-list">
      <h2>Your Boards</h2>
      <ul>
        {boards.map(board => (
          <li key={board.id} onClick={() => setCurrentBoard(board)}>
            {board.name}
          </li>
        ))}
      </ul>
      <button onClick={() => setCurrentBoard({ id: null, name: '' })}>Create New Board</button>
    </div>
  );
};

const Board = ({ board, setCurrentBoard, columns, setColumns, tasks, setTasks }) => {
  const [newColumnName, setNewColumnName] = useState('');

  const addColumn = async () => {
    try {
      const newColumn = await fetchData(`/boards/${board.id}/columns`, 'POST', { name: newColumnName });
      setColumns([...columns, newColumn]);
      setNewColumnName('');
    } catch (error) {
      console.error('Error adding column:', error);
    }
  };

  const moveColumn = async (columnId, newPosition) => {
    try {
      const updatedColumn = await fetchData(`/columns/${columnId}`, 'PUT', { position: newPosition });
      setColumns(columns.map(col => col.id === columnId ? updatedColumn : col));
    } catch (error) {
      console.error('Error moving column:', error);
    }
  };

  const deleteColumn = async (columnId) => {
    try {
      await fetchData(`/columns/${columnId}`, 'DELETE');
      setColumns(columns.filter(col => col.id !== columnId));
      setTasks(tasks.filter(task => task.column_id !== columnId));
    } catch (error) {
      console.error('Error deleting column:', error);
    }
  };

  return (
    <div className="board">
      <h2>{board.name}</h2>
      <button onClick={() => setCurrentBoard(null)}>Back to Boards</button>
      <div className="columns">
        {columns.sort((a, b) => a.position - b.position).map(column => (
          <Column
            key={column.id}
            column={column}
            tasks={tasks.filter(task => task.column_id === column.id)}
            setTasks={setTasks}
            moveColumn={moveColumn}
            deleteColumn={deleteColumn}
          />
        ))}
        <div className="new-column">
          <input
            type="text"
            value={newColumnName}
            onChange={(e) => setNewColumnName(e.target.value)}
            placeholder="New Column Name"
          />
          <button onClick={addColumn}>Add Column</button>
        </div>
      </div>
    </div>
  );
};

const Column = ({ column, tasks, setTasks, moveColumn, deleteColumn }) => {
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');

  const addTask = async () => {
    try {
      const newTask = await fetchData(`/columns/${column.id}/tasks`, 'POST', {
        title: newTaskTitle,
        description: newTaskDescription
      });
      setTasks([...tasks, newTask]);
      setNewTaskTitle('');
      setNewTaskDescription('');
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const moveTask = async (taskId, newPosition, newColumnId) => {
    try {
      const updatedTask = await fetchData(`/tasks/${taskId}`, 'PUT', { position: newPosition, column_id: newColumnId });
      setTasks(tasks.map(task => task.id === taskId ? updatedTask : task));
    } catch (error) {
      console.error('Error moving task:', error);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await fetchData(`/tasks/${taskId}`, 'DELETE');
      setTasks(tasks.filter(task => task.id !== taskId));
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  return (
    <div className="column" style={{ order: column.position }}>
      <div className="column-header">
        <h3>{column.name}</h3>
        <button onClick={() => moveColumn(column.id, column.position - 1)} disabled={column.position === 0}>↑</button>
        <button onClick={() => moveColumn(column.id, column.position + 1)} disabled={column.position === columns.length - 1}>↓</button>
        <button onClick={() => deleteColumn(column.id)}>Delete</button>
      </div>
      <div className="tasks">
        {tasks.sort((a, b) => a.position - b.position).map(task => (
          <Task
            key={task.id}
            task={task}
            moveTask={moveTask}
            deleteTask={deleteTask}
          />
        ))}
      </div>
      <div className="new-task">
        <input
          type="text"
          value={newTaskTitle}
          onChange={(e) => setNewTaskTitle(e.target.value)}
          placeholder="Task Title"
        />
        <textarea
          value={newTaskDescription}
          onChange={(e) => setNewTaskDescription(e.target.value)}
          placeholder="Task Description"
        />
        <button onClick={addTask}>Add Task</button>
      </div>
    </div>
  );
};

const Task = ({ task, moveTask, deleteTask }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartY, setDragStartY] = useState(0);
  const [dragOffsetY, setDragOffsetY] = useState(0);

  const handleDragStart = (e) => {
    setIsDragging(true);
    setDragStartY(e.clientY);
    e.dataTransfer.setData('text/plain', JSON.stringify({ taskId: task.id, columnId: task.column_id }));
  };

  const handleDrag = (e) => {
    if (isDragging) {
      setDragOffsetY(e.clientY - dragStartY);
    }
  };

  const handleDragEnd = (e) => {
    setIsDragging(false);
    setDragOffsetY(0);

    const dropData = JSON.parse(e.dataTransfer.getData('text/plain'));
    if (dropData.taskId === task.id) {
      const newPosition = tasks.findIndex(t => t.id === task.id);
      moveTask(task.id, newPosition, task.column_id);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropData = JSON.parse(e.dataTransfer.getData('text/plain'));
    if (dropData.taskId !== task.id) {
      const newPosition = tasks.findIndex(t => t.id === task.id);
      moveTask(dropData.taskId, newPosition, task.column_id);
    }
  };

  return (
    <div
      className="task"
      draggable="true"
      onDragStart={handleDragStart}
      onDrag={handleDrag}
      onDragEnd={handleDragEnd}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
      style={{ transform: isDragging ? `translateY(${dragOffsetY}px)` : 'none' }}
    >
      <h4>{task.title}</h4>
      <p>{task.description}</p>
      <button onClick={() => deleteTask(task.id)}>Delete</button>
    </div>
  );
};

// Main App component
const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [boards, setBoards] = useState([]);
  const [currentBoard, setCurrentBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    if (token) {
      fetchBoards();
    }
  }, [token]);

  useEffect(() => {
    if (currentBoard) {
      fetchBoardData();
    }
  }, [currentBoard]);

  const fetchBoards = async () => {
    try {
      const data = await fetchData('/boards');
      setBoards(data);
    } catch (error) {
      console.error('Error fetching boards:', error);
      setToken(null);
      localStorage.removeItem('token');
    }
  };

  const fetchBoardData = async () => {
    try {
      const boardData = await fetchData(`/boards/${currentBoard.id}`);
      setColumns(boardData.columns);

      const tasksData = await fetchData(`/boards/${currentBoard.id}/tasks`);
      setTasks(tasksData);
    } catch (error) {
      console.error('Error fetching board data:', error);
    }
  };

  const createBoard = async (name) => {
    try {
      const newBoard = await fetchData('/boards', 'POST', { name });
      setBoards([...boards, newBoard]);
      setCurrentBoard(newBoard);
    } catch (error) {
      console.error('Error creating board:', error);
    }
  };

  const updateBoard = async (id, name) => {
    try {
      const updatedBoard = await fetchData(`/boards/${id}`, 'PUT', { name });
      setBoards(boards.map(board => board.id === id ? updatedBoard : board));
      setCurrentBoard(updatedBoard);
    } catch (error) {
      console.error('Error updating board:', error);
    }
  };

  const deleteBoard = async (id) => {
    try {
      await fetchData(`/boards/${id}`, 'DELETE');
      setBoards(boards.filter(board => board.id !== id));
      setCurrentBoard(null);
      setColumns([]);
      setTasks([]);
    } catch (error) {
      console.error('Error deleting board:', error);
    }
  };

  if (!token) {
    return <Login setToken={setToken} />;
  }

  return (
    <div className="app">
      {currentBoard ? (
        <Board
          board={currentBoard}
          setCurrentBoard={setCurrentBoard}
          columns={columns}
          setColumns={setColumns}
          tasks={tasks}
          setTasks={setTasks}
        />
      ) : (
        <BoardList boards={boards} setCurrentBoard={setCurrentBoard} />
      )}
    </div>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
