// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';

// 1. Imports
import './App.css';

// 2. State Management
const App = () => {
  const [posts, setPosts] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [newPost, setNewPost] = useState({ title: '', content: '' });

  // 3. Lifecycle Functions
  useEffect(() => {
    fetchPosts();
  }, []);

  // 4. Event Handlers
  const handleLogin = async () => {
    try {
      const response = await axios.post('http://localhost:5099/login', { username, password });
      setToken(response.data.access_token);
      localStorage.setItem('token', response.data.access_token);
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:5099/register', { username, password });
      alert('Registration successful!');
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  const handleCreatePost = async () => {
    try {
      await axios.post('http://localhost:5099/posts', newPost, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      fetchPosts();
    } catch (error) {
      console.error('Post creation failed:', error);
    }
  };

  const fetchPosts = async () => {
    try {
      const response = await axios.get('http://localhost:5099/posts');
      setPosts(response.data);
    } catch (error) {
      console.error('Fetching posts failed:', error);
    }
  };

  // 5. API Calls
  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
  };

  // UI Components
  return (
    <Router>
      <div>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
          <Link to="/create-post">Create Post</Link>
          {token && <button onClick={handleLogout}>Logout</button>}
        </nav>
        <Switch>
          <Route path="/login">
            <div>
              <h2>Login</h2>
              <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button onClick={handleLogin}>Login</button>
            </div>
          </Route>
          <Route path="/register">
            <div>
              <h2>Register</h2>
              <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button onClick={handleRegister}>Register</button>
            </div>
          </Route>
          <Route path="/create-post">
            <div>
              <h2>Create Post</h2>
              <input type="text" placeholder="Title" value={newPost.title} onChange={(e) => setNewPost({ ...newPost, title: e.target.value })} />
              <textarea placeholder="Content" value={newPost.content} onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}></textarea>
              <button onClick={handleCreatePost}>Create Post</button>
            </div>
          </Route>
          <Route path="/">
            <div>
              <h2>Posts</h2>
              <ul>
                {posts.map((post) => (
                  <li key={post.id}>
                    <h3>{post.title}</h3>
                    <p>{post.content}</p>
                  </li>
                ))}
              </ul>
            </div>
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
