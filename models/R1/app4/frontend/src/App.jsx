import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import marked from 'marked';
import './App.css';

// Configure axios
axios.defaults.baseURL = 'http://localhost:5567/api';

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [categories] = useState(['Technology', 'Lifestyle', 'Travel']);
  const navigate = useNavigate();

  // Check existing session
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get('/posts').then(() => setUser({ id: localStorage.getItem('userId') }));
    }
  }, []);

  // Fetch posts
  useEffect(() => {
    axios.get('/posts').then(res => setPosts(res.data));
  }, []);

  // Authentication Handlers
  const handleLogin = async (credentials) => {
    try {
      const res = await axios.post('/login', credentials);
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('userId', res.data.user_id);
      setUser({ id: res.data.user_id });
      navigate('/');
    } catch (err) {
      alert('Login failed');
    }
  };

  const handleRegister = async (credentials) => {
    try {
      await axios.post('/register', credentials);
      alert('Registration successful. Please login.');
      navigate('/login');
    } catch (err) {
      alert('Registration failed');
    }
  };

  // Components
  const Login = () => (
    <div className="auth-form">
      <h2>Login</h2>
      <form onSubmit={e => {
        e.preventDefault();
        handleLogin({
          username: e.target.username.value,
          password: e.target.password.value
        });
      }}>
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Login</button>
      </form>
    </div>
  );

  const Register = () => (
    <div className="auth-form">
      <h2>Register</h2>
      <form onSubmit={e => {
        e.preventDefault();
        handleRegister({
          username: e.target.username.value,
          password: e.target.password.value
        });
      }}>
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">Register</button>
      </form>
    </div>
  );

  const PostList = () => (
    <div className="posts-container">
      {posts.map(post => (
        <div key={post.id} className="post-card">
          <h3>{post.title}</h3>
          <div className="post-meta">
            <span>By {post.author}</span>
            <span>{new Date(post.created_at).toLocaleDateString()}</span>
          </div>
          <div dangerouslySetInnerHTML={{ __html: post.content }} />
        </div>
      ))}
    </div>
  );

  return (
    <main>
      <nav className="navbar">
        <h1>Blog Platform</h1>
        <div className="nav-items">
          {user ? (
            <button onClick={() => {
              localStorage.clear();
              setUser(null);
              navigate('/login');
            }}>Logout</button>
          ) : (
            <>
              <button onClick={() => navigate('/login')}>Login</button>
              <button onClick={() => navigate('/register')}>Register</button>
            </>
          )}
        </div>
      </nav>

      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PostList />} />
      </Routes>
    </main>
  );
}

// Mounting Logic
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>
);
