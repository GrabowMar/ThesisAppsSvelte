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
  const [showAddColumn, setShowAddColumn] = useState(false);
  const [newColumnName, setNewColumnName] = useState('');
  
  // Load board data
  const fetchBoardData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiClient.get(`/boards/${boardId}`);
      setBoard(data.board);
      setColumns(data.columns);
      setTasks(data.tasks);
    } catch (err) {
      setError('Failed to load board data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [boardId]);

  useEffect(() => {
    fetchBoardData();
  }, [fetchBoardData]);

  // Task operations
  const handleAddTask = async (columnId, taskData) => {
    try {
      const newTask = await apiClient.post(`/columns/${columnId}/tasks`, taskData);
      setTasks(prev => ({
        ...prev,
        [columnId]: [...(prev[columnId] || []), newTask]
      }));
    } catch (err) {
      console.error('Failed to add task:', err);
      alert('Failed to add task');
    }
  };

  const handleTaskUpdate = async (taskId, taskData) => {
    try {
      const updatedTask = await apiClient.put(`/tasks/${taskId}`, taskData);
      
      // Update tasks state
      setTasks(prev => {
        const newTasks = { ...prev };
        
        // Find which column contains this task
        for (const columnId in newTasks) {
          const taskIndex = newTasks[columnId].findIndex(t => t.id === taskId);
          if (taskIndex !== -1) {
            // Replace the task with the updated version
            newTasks[columnId] = [
              ...newTasks[columnId].slice(0, taskIndex),
              updatedTask,
              ...newTasks[columnId].slice(taskIndex + 1)
            ];
            break;
          }
        }
        
        return newTasks;
      });
    } catch (err) {
      console.error('Failed to update task:', err);
      alert('Failed to update task');
    }
  };

  const handleTaskDelete = async (taskId) => {
    try {
      await apiClient.delete(`/tasks/${taskId}`);
      
      // Remove task from state
      setTasks(prev => {
        const newTasks = { ...prev };
        
        for (const columnId in newTasks) {
          const taskIndex = newTasks[columnId].findIndex(t => t.id === taskId);
          if (taskIndex !== -1) {
            newTasks[columnId] = [
              ...newTasks[columnId].slice(0, taskIndex),
              ...newTasks[columnId].slice(taskIndex + 1)
            ];
            break;
          }
        }
        
        return newTasks;
      });
    } catch (err) {
      console.error('Failed to delete task:', err);
      alert('Failed to delete task');
    }
  };

  const handleTaskMove = async (taskId, sourceColumnId, targetColumnId) => {
    try {
      // Find the task in the source column
      const taskIndex = tasks[sourceColumnId].findIndex(t => t.id === taskId);
      if (taskIndex === -1) return;
      
      const taskToMove = tasks[sourceColumnId][taskIndex];
      
      // Add to the bottom of target column
      const position = tasks[targetColumnId] ? tasks[targetColumnId].length : 0;
      
      // Update the task on the server
      const updatedTask = await apiClient.put(`/tasks/${taskId}`, {
        column_id: targetColumnId,
        position
      });
      
      // Update local state
      setTasks(prev => {
        const newTasks = { ...prev };
        
        // Remove from source column
        newTasks[sourceColumnId] = [
          ...newTasks[sourceColumnId].slice(0, taskIndex),
          ...newTasks[sourceColumnId].slice(taskIndex + 1)
        ];
        
        // Add to target column
        newTasks[targetColumnId] = [
          ...(newTasks[targetColumnId] || []),
          updatedTask
        ];
        
        return newTasks;
      });
    } catch (err) {
      console.error('Failed to move task:', err);
      alert('Failed to move task');
    }
  };

  // Column operations
  const handleAddColumn = async () => {
    if (!newColumnName.trim()) return;
    
    try {
      const newColumn = await apiClient.post(`/boards/${boardId}/columns`, {
        name: newColumnName
      });
      
      setColumns(prev => [...prev, newColumn]);
      setTasks(prev => ({ ...prev, [newColumn.id]: [] }));
      setNewColumnName('');
      setShowAddColumn(false);
    } catch (err) {
      console.error('Failed to add column:', err);
      alert('Failed to add column');
    }
  };

  const handleColumnUpdate = async (columnId, columnData) => {
    try {
      const updatedColumn = await apiClient.put(`/columns/${columnId}`, columnData);
      
      setColumns(prev => 
        prev.map(col => col.id === columnId ? updatedColumn : col)
      );
    } catch (err) {
      console.error('Failed to update column:', err);
      alert('Failed to update column');
    }
  };

  const handleColumnDelete = async (columnId) => {
    try {
      await apiClient.delete(`/columns/${columnId}`);
      
      setColumns(prev => prev.filter(col => col.id !== columnId));
      
      // Remove tasks for this column
      setTasks(prev => {
        const newTasks = { ...prev };
        delete newTasks[columnId];
        return newTasks;
      });
    } catch (err) {
      console.error('Failed to delete column:', err);
      alert('Failed to delete column');
    }
  };

  if (loading) {
    return <div className="loading">Loading board...</div>;
  }

  if (error) {
    return (
      <div className="error-state">
        <p>{error}</p>
        <button onClick={onBackToList}>Back to Boards</button>
      </div>
    );
  }

  if (!board) {
    return (
      <div className="error-state">
        <p>Board not found</p>
        <button onClick={onBackToList}>Back to Boards</button>
      </div>
    );
  }

  return (
    <div className="board-view">
      <div className="board-header">
        <button className="back-button" onClick={onBackToList}>
          &larr; Back to Boards
        </button>
        <h2>{board.name}</h2>
      </div>

      <div className="board-columns">
        {columns.map(column => (
          <Column
            key={column.id}
            column={column}
            tasks={tasks[column.id] || []}
            onAddTask={handleAddTask}
            onTaskUpdate={handleTaskUpdate}
            onTaskDelete={handleTaskDelete}
            onTaskMove={handleTaskMove}
            onColumnUpdate={handleColumnUpdate}
            onColumnDelete={handleColumnDelete}
          />
        ))}
        
        {showAddColumn ? (
          <div className="add-column-form">
            <input
              type="text"
              value={newColumnName}
              onChange={(e) => setNewColumnName(e.target.value)}
              placeholder="Column name"
              autoFocus
            />
            <div className="add-column-actions">
              <button onClick={handleAddColumn}>Add</button>
              <button onClick={() => setShowAddColumn(false)}>Cancel</button>
            </div>
          </div>
        ) : (
          <button 
            className="add-column-btn"
            onClick={() => setShowAddColumn(true)}
          >
            + Add Column
          </button>
        )}
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { logout } = React.useContext(AuthContext);
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedBoard, setSelectedBoard] = useState(null);

  const fetchBoards = useCallback(async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await apiClient.get('/boards');
      setBoards(data);
    } catch (err) {
      setError('Failed to load boards');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBoards();
  }, [fetchBoards]);

  const handleBoardCreate = async (name) => {
    try {
      const newBoard = await apiClient.post('/boards', { name });
      setBoards(prev => [...prev, newBoard]);
    } catch (err) {
      console.error('Failed to create board:', err);
      alert('Failed to create board');
    }
  };

  const handleBoardDelete = async (boardId) => {
    try {
      await apiClient.delete(`/boards/${boardId}`);
      setBoards(prev => prev.filter(b => b.id !== boardId));
      
      // If the deleted board was selected, go back to the list
      if (selectedBoard === boardId) {
        setSelectedBoard(null);
      }
    } catch (err) {
      console.error('Failed to delete board:', err);
      alert('Failed to delete board');
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (selectedBoard) {
    return (
      <BoardView 
        boardId={selectedBoard} 
        onBackToList={() => setSelectedBoard(null)} 
      />
    );
  }

  return (
    <div className="dashboard">
      <header className="app-header">
        <h1>Kanban Boards</h1>
        <button className="logout-btn" onClick={logout}>Logout</button>
      </header>
      
      {error && <div className="error-message">{error}</div>}
      
      <BoardsList 
        boards={boards}
        onBoardSelect={setSelectedBoard}
        onBoardCreate={handleBoardCreate}
        onBoardDelete={handleBoardDelete}
      />
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const userData = await apiClient.get('/user');
        setUser(userData);
      } catch (error) {
        console.error('Auth check failed:', error);
        removeToken();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = useCallback((userData) => {
    setUser(userData);
  }, []);

  const logout = useCallback(() => {
    removeToken();
    setUser(null);
  }, []);

  const authContextValue = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
  };

  if (loading) {
    return <div className="loading">Loading application...</div>;
  }

  return (
    <AuthContext.Provider value={authContextValue}>
      <DndProvider backend={HTML5Backend}>
        <div className="app">
          {user ? <Dashboard /> : <AuthScreen />}
        </div>
      </DndProvider>
    </AuthContext.Provider>
  );
};

// Mount the application to the DOM
const root = createRoot(document.getElementById('root'));
root.render(<App />);

export default App;


