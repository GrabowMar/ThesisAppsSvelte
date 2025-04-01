// app/frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Link, useLoaderData, useNavigate, useParams } from "react-router-dom";
import ReactDOM from 'react-dom/client';
import './App.css';

// API base URL (assumes proxy via Vite config)
const API_BASE = '/api';

// -------------
// Helper Functions
// -------------
const fetchAPI = async (endpoint, options = {}) => {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!res.ok) {
    const errorData = await res.json();
    throw new Error(errorData.error || "API request failed");
  }
  return res.json();
};

// -------------
// Views / Components
// -------------

// Home / Threads List
function Threads() {
  const [threads, setThreads] = useState([]);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [sort, setSort] = useState('desc');
  const [newThread, setNewThread] = useState({ title: '', content: '', category: '', author: '' });

  const loadThreads = async () => {
    try {
      let query = `?search=${search}&category=${category}&sort=${sort}`;
      const data = await fetchAPI(`/threads${query}`);
      setThreads(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadThreads();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, category, sort]);

  const handleThreadSubmit = async (e) => {
    e.preventDefault();
    try {
      const created = await fetchAPI('/threads', {
        method: "POST",
        body: JSON.stringify(newThread)
      });
      setNewThread({ title: '', content: '', category: '', author: '' });
      loadThreads();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h2>Forum Threads</h2>
      {error && <div className="error">{error}</div>}
      <div className="search">
        <input 
          type="text" placeholder="Search threads..." 
          value={search} onChange={(e) => setSearch(e.target.value)}
        />
        <input 
          type="text" placeholder="Category filter..." 
          value={category} onChange={(e) => setCategory(e.target.value)}
        />
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="desc">Newest first</option>
          <option value="asc">Oldest first</option>
        </select>
      </div>
      <ul className="thread-list">
        {threads.map(thread => (
          <li key={thread.id}>
            <Link to={`/thread/${thread.id}`}>{thread.title}</Link>
            <span className="thread-meta"> - {thread.category} - By {thread.author} at {new Date(thread.created_at).toLocaleString()}</span>
          </li>
        ))}
      </ul>
      <h3>Create a new Thread</h3>
      <form onSubmit={handleThreadSubmit} className="form">
        <input type="text" placeholder="Title" required value={newThread.title} onChange={(e) => setNewThread({...newThread, title: e.target.value})} />
        <textarea placeholder="Content" required value={newThread.content} onChange={(e) => setNewThread({...newThread, content: e.target.value})}></textarea>
        <input type="text" placeholder="Category" value={newThread.category} onChange={(e) => setNewThread({...newThread, category: e.target.value})} />
        <input type="text" placeholder="Author" required value={newThread.author} onChange={(e) => setNewThread({...newThread, author: e.target.value})} />
        <button type="submit">Create Thread</button>
      </form>
    </div>
  );
}

// Thread Details and Comments
function ThreadDetail() {
  const { threadId } = useParams();
  const [thread, setThread] = useState(null);
  const [error, setError] = useState('');
  const [newComment, setNewComment] = useState({ content: '', author: '' });

  const loadThread = async () => {
    try {
      const data = await fetchAPI(`/threads/${threadId}`);
      setThread(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadThread();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [threadId]);

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    try {
      await fetchAPI(`/threads/${threadId}/comments`, {
        method: "POST",
        body: JSON.stringify(newComment)
      });
      setNewComment({ content: '', author: '' });
      loadThread();
    } catch (err) {
      setError(err.message);
    }
  };

  if (!thread) return <div className="container">Loading thread...</div>;
  return (
    <div className="container">
      <h2>{thread.title}</h2>
      <p>{thread.content}</p>
      <p className="thread-meta">Category: {thread.category} - Author: {thread.author} - Posted at: {new Date(thread.created_at).toLocaleString()}</p>
      
      <h3>Comments</h3>
      <ul className="comment-list">
        {thread.comments && thread.comments.length > 0 ? (
          thread.comments.map(comment => (
            <li key={comment.id}>
              <p>{comment.content}</p>
              <span className="comment-meta">By {comment.author} at {new Date(comment.created_at).toLocaleString()}</span>
            </li>
          ))
        ) : (
          <li>No comments yet.</li>
        )}
      </ul>

      <h4>Add a Comment</h4>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleCommentSubmit} className="form">
        <textarea placeholder="Your comment..." required value={newComment.content} onChange={(e) => setNewComment({...newComment, content: e.target.value})}></textarea>
        <input type="text" placeholder="Your name" required value={newComment.author} onChange={(e) => setNewComment({...newComment, author: e.target.value})} />
        <button type="submit">Post Comment</button>
      </form>
    </div>
  );
}

// Login Page
function Login() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetchAPI('/login', {
        method: "POST",
        body: JSON.stringify(credentials)
      });
      // In production, store token or user session
      navigate('/dashboard');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleLogin} className="form">
        <input type="text" placeholder="Username" required value={credentials.username} onChange={(e) => setCredentials({...credentials, username: e.target.value})} />
        <input type="password" placeholder="Password" required value={credentials.password} onChange={(e) => setCredentials({...credentials, password: e.target.value})} />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

// Register Page
function Register() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetchAPI('/register', {
        method: "POST",
        body: JSON.stringify(credentials)
      });
      navigate('/login');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container">
      <h2>Register</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleRegister} className="form">
        <input type="text" placeholder="Username" required value={credentials.username} onChange={(e) => setCredentials({...credentials, username: e.target.value})} />
        <input type="password" placeholder="Password" required value={credentials.password} onChange={(e) => setCredentials({...credentials, password: e.target.value})} />
        <button type="submit">Register</button>
      </form>
    </div>
  );
}

// Dashboard Page
function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');
  const loadDashboard = async () => {
    try {
      const data = await fetchAPI('/dashboard');
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => { loadDashboard(); }, []);

  return (
    <div className="container">
      <h2>Dashboard</h2>
      {error && <div className="error">{error}</div>}
      {stats ? (
        <div>
          <p>{stats.message}</p>
          <p>Threads: {stats.threads_count}</p>
          <p>Users Registered: {stats.users_count}</p>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}

// Navigation Bar
function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/">Threads</Link>
      <Link to="/login">Login</Link>
      <Link to="/register">Register</Link>
      <Link to="/dashboard">Dashboard</Link>
    </nav>
  );
}

// -------------
// Router Setup
// -------------

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <>
        <NavBar />
        <Threads />
      </>
    )
  },
  {
    path: "thread/:threadId",
    element: (
      <>
        <NavBar />
        <ThreadDetail />
      </>
    )
  },
  {
    path: "login",
    element: (
      <>
        <NavBar />
        <Login />
      </>
    )
  },
  {
    path: "register",
    element: (
      <>
        <NavBar />
        <Register />
      </>
    )
  },
  {
    path: "dashboard",
    element: (
      <>
        <NavBar />
        <Dashboard />
      </>
    )
  }
]);

// -------------
// Main App Component
// -------------
function App() {
  return <RouterProvider router={router} />;
}

// -------------
// Mounting Logic
// -------------
const rootElement = document.getElementById("root");
if (rootElement) {
  ReactDOM.createRoot(rootElement).render(<App />);
} else {
  console.error('Failed to find the root element');
}

export default App;
