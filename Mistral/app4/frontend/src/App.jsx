// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import axios from 'axios';

// 2. State Management
const App = () => {
  const [posts, setPosts] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  useEffect(() => {
    axios.get('/api/posts')
      .then(response => setPosts(response.data))
      .catch(error => console.error('Error fetching posts:', error));
  }, []);

  const handleLogin = (email, password) => {
    axios.post('/api/login', { email, password })
      .then(response => {
        setToken(response.data.access_token);
        localStorage.setItem('token', response.data.access_token);
      })
      .catch(error => console.error('Error logging in:', error));
  };

  const handleRegister = (username, email, password) => {
    axios.post('/api/register', { username, email, password })
      .then(response => console.log('User registered:', response.data))
      .catch(error => console.error('Error registering:', error));
  };

  const handleCreatePost = (title, content) => {
    axios.post('/api/posts', { title, content }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(response => console.log('Post created:', response.data))
      .catch(error => console.error('Error creating post:', error));
  };

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
        <Link to="/create-post">Create Post</Link>
      </nav>
      <Switch>
        <Route path="/" exact>
          <h1>Blog</h1>
          {posts.map(post => (
            <div key={post.id}>
              <h2>{post.title}</h2>
              <p>{post.content}</p>
              <p>{post.date_posted}</p>
              <p>{post.author}</p>
            </div>
          ))}
        </Route>
        <Route path="/login">
          <Login handleLogin={handleLogin} />
        </Route>
        <Route path="/register">
          <Register handleRegister={handleRegister} />
        </Route>
        <Route path="/create-post">
          <CreatePost handleCreatePost={handleCreatePost} />
        </Route>
      </Switch>
    </Router>
  );
};

const Login = ({ handleLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div>
      <h2>Login</h2>
      <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
      <button onClick={() => handleLogin(email, password)}>Login</button>
    </div>
  );
};

const Register = ({ handleRegister }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div>
      <h2>Register</h2>
      <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
      <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" />
      <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" />
      <button onClick={() => handleRegister(username, email, password)}>Register</button>
    </div>
  );
};

const CreatePost = ({ handleCreatePost }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  return (
    <div>
      <h2>Create Post</h2>
      <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" />
      <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Content" />
      <button onClick={() => handleCreatePost(title, content)}>Create Post</button>
    </div>
  );
};

// 8. Mounting Logic
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
