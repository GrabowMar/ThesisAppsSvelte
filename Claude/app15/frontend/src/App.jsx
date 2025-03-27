import React, { useState, useEffect, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import './App.css';

// Constants
const API_BASE_URL = 'http://localhost:5349/api';

// Auth Context
const AuthContext = React.createContext(null);

// Utility Functions
const setToken = (token) => {
  localStorage.setItem('kanbanToken', token);
};

const getToken = () => {
  return localStorage.getItem('kanbanToken');
};

const removeToken = () => {
  localStorage.removeItem('kanbanToken');
};

// API Client with Auth
const apiClient = {
  request: async (endpoint, options = {}) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Something went wrong');
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },

  get: (endpoint) => {
    return apiClient.request(endpoint, { method: 'GET' });
  },

  post: (endpoint, body) => {
    return apiClient.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  put: (endpoint, body) => {
    return apiClient.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  delete: (endpoint) => {
    return apiClient.request(endpoint, { method: 'DELETE' });
  },
};

// Components
const LoginForm = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const data = await apiClient.post('/login', { email, password });
      setToken(data.access_token);
      onLogin(data.user);
    } catch (error) {
      setError(error.message || 'Failed to login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Login</h2>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

const RegisterForm = ({ onRegister }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const data = await apiClient.post('/register', { name, email, password });
      setToken(data.access_token);
      onRegister(data.user);
    } catch (error) {
      setError(error.message || 'Failed to register');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>Register</h2>
      {error && <div className="error-message">{error}</div>}
      <div className="form-group">
        <label htmlFor="name">Name</label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength="6"
          required
        />
      </div>
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Registering...' : 'Register'}
      </button>
    </form>
  );
};

const AuthScreen = () => {
  const [showLogin, setShowLogin] = useState(true);
  const { login } = React.useContext(AuthContext);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Kanban Board</h1>
          <div className="auth-tabs">
            <button
              className={showLogin ? 'active' : ''}
              onClick={() => setShowLogin(true)}
            >
              Login
            </button>
            <button
              className={!showLogin ? 'active' : ''}
              onClick={() => setShowLogin(false)}
            >
              Register
            </button>
          </div>
        </div>
        {showLogin ? (
          <LoginForm onLogin={login} />
        ) : (
          <RegisterForm onRegister={login} />
        )}
      </div>
    </div>
  );
};

const TaskCard = ({ task, columnId, onTaskUpdate, onTaskDelete }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: 'TASK',
    item: { id: task.id, columnId, taskData: task },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  }));

  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || '');

  const handleSave = () => {
    onTaskUpdate(task.id, { title, description });
    setIsEditing(false);
  };

  return (
    <div
      ref={drag}
      className={`task-card ${isDragging ? 'dragging' : ''}`}
      onClick={() => !isDragging && setIsEditing(true)}
    >
      {isEditing ? (
        <div className="task-edit-form" onClick={(e) => e.stopPropagation()}>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Task title"
            autoFocus
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
            rows={3}
          />
          <div className="task-edit-actions">
            <button onClick={handleSave}>Save</button>
            <button onClick={() => onTaskDelete(task.id)}>Delete</button>
            <button onClick={() => setIsEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <h4>{task.title}</h4>
          {task.description && <p>{task.description}</p>}
        </>
      )}
    </div>
  );
};

const Column = ({ column, tasks = [], onAddTask, onTaskUpdate, onTaskDelete, onColumnUpdate, onColumnDelete, onTaskMove }) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: 'TASK',
    drop: (item) => {
      if (item.columnId !== column.id) {
        onTaskMove(item.id, item.columnId, column.id);
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  }));

  const [isEditing, setIsEditing] = useState(false);
  const [columnName, setColumnName] = useState(column.name);
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTaskTitle, setNewTaskTitle] = useState('');
  const [newTaskDescription, setNewTaskDescription] = useState('');

  const handleAddTask = () => {
    if (newTaskTitle.trim()) {
      onAddTask(column.id, {
        title: newTaskTitle,
        description: newTaskDescription,
      });
      setNewTaskTitle('');
      setNewTaskDescription('');
      setShowAddTask(false);
    }
  };

  const handleColumnUpdate = () => {
    if (columnName.trim()) {
      onColumnUpdate(column.id, { name: columnName });
      setIsEditing(false);
    }
  };

  return (
    <div className={`column ${isOver ? 'drop-target' : ''}`} ref={drop}>
      <div className="column-header">
        {isEditing ? (
          <div className="column-edit">
            <input
              type="text"
              value={columnName}
              onChange={(e) => setColumnName(e.target.value)}
              autoFocus
            />
            <div className="column-edit-actions">
              <button onClick={handleColumnUpdate}>Save</button>
              <button onClick={() => onColumnDelete(column.id)}>Delete</button>
              <button onClick={() => setIsEditing(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          <>
            <h3 onClick={() => setIsEditing(true)}>{column.name}</h3>
            <button
              className="add-task-btn"
              onClick={() => setShowAddTask(true)}
            >
              +
            </button>
          </>
        )}
      </div>
      
      {showAddTask && (
        <div className="add-task-form">
          <input
            type="text"
            value={newTaskTitle}
            onChange={(e) => setNewTaskTitle(e.target.value)}
            placeholder="Task title"
            autoFocus
          />
          <textarea
            value={newTaskDescription}
            onChange={(e) => setNewTaskDescription(e.target.value)}
            placeholder="Description (optional)"
            rows={3}
          />
          <div className="add-task-actions">
            <button onClick={handleAddTask}>Add</button>
            <button onClick={() => setShowAddTask(false)}>Cancel</button>
          </div>
        </div>
      )}

      <div className="task-list">
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            columnId={column.id}
            onTaskUpdate={onTaskUpdate}
            onTaskDelete={onTaskDelete}
          />
        ))}
      </div>
    </div>
  );
};

const BoardsList = ({ boards, onBoardSelect, onBoardCreate, onBoardDelete }) => {
  const [newBoardName, setNewBoardName] = useState('');
  const [showForm, setShowForm] = useState(false);

  const handleCreateBoard = () => {
    if (newBoardName.trim()) {
      onBoardCreate(newBoardName);
      setNewBoardName('');
      setShowForm(false);
    }
  };

  return (
    <div className="boards-list">
      <h2>Your Boards</h2>
      
      {showForm ? (
        <div className="add-board-form">
          <input
            type="text"
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
            placeholder="Board name"
            autoFocus
          />
          <div className="add-board-actions">
            <button onClick={handleCreateBoard}>Create</button>
            <button onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button className="new-board-btn" onClick={() => setShowForm(true)}>
          + New Board
        </button>
      )}

      <ul className="boards-grid">
        {boards.map((board) => (
          <li key={board.id} className="board-item">
            <div 
              className="board-card"
              onClick={() => onBoardSelect(board.id)}
            >
              <h3>{board.name}</h3>
              <p>Created: {new Date(board.created_at).toLocaleDateString()}</p>
            </div>
            <button
              className="delete-board-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm(`Delete board "${board.name}"?`)) {
                  onBoardDelete(board.id);
                }
              }}
            >
              🗑️
            </button>
          </li>
        ))}
      </ul>
      
      {boards.length === 0 && !showForm && (
        <div className="empty-state">
          <p>You don't have any boards yet. Create one to get started!</p>
        </div>
      )}
    </div>
  );
};

const BoardView = ({ boardId, onBackToList }) => {
  const [board, setBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const
