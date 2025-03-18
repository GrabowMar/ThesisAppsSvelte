import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5099';

const Register = () => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '' });
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/register`, formData);
      alert('User registered successfully');
    } catch (error) {
      alert('Error registering user');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="username" placeholder="Username" onChange={handleChange} required />
      <input type="email" name="email" placeholder="Email" onChange={handleChange} required />
      <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
      <button type="submit">Register</button>
    </form>
  );
};

const Login = ({ setUserId }) => {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API_URL}/login`, formData);
      setUserId(response.data.user_id);
      alert('Login successful');
    } catch (error) {
      alert('Error logging in');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="email" name="email" placeholder="Email" onChange={handleChange} required />
      <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
      <button type="submit">Login</button>
    </form>
  );
};

const Dashboard = ({ userId }) => {
  const [posts, setPosts] = useState([]);
  const [newPost, setNewPost] = useState({ title: '', content: '' });

  useEffect(() => {
    const fetchPosts = async () => {
      const response = await axios.get(`${API_URL}/posts`);
      setPosts(response.data);
    };
    fetchPosts();
  }, []);

  const handleChange = (e) => {
    setNewPost({ ...newPost, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/posts`, { ...newPost, user_id: userId });
      setNewPost({ title: '', content: '' });
      const response = await axios.get(`${API_URL}/posts`);
      setPosts(response.data);
    } catch (error) {
      alert('Error creating post');
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input type="text" name="title" placeholder="Title" onChange={handleChange} value={newPost.title} required />
        <textarea name="content" placeholder="Content" onChange={handleChange} value={newPost.content} required></textarea>
        <button type="submit">Create Post</button>
      </form>
      <div>
        {posts.map(post => (
          <div key={post.id}>
            <h3>{post.title}</h3>
            <p>{post.content}</p>
            <button onClick={() => likePost(post.id)}>Like ({post.likes})</button>
            <button onClick={() => commentPost(post.id)}>Comment</button>
          </div>
        ))}
      </div>
    </div>
  );
};

const likePost = async (postId) => {
  try {
    await axios.post(`${API_URL}/posts/${postId}/like`);
    alert('Post liked successfully');
  } catch (error) {
    alert('Error liking post');
  }
};

const commentPost = async (postId) => {
  const comment = prompt('Enter your comment:');
  try {
    await axios.post(`${API_URL}/posts/${postId}/comment`, { content: comment, user_id: 1 }); // Hardcoded user_id for demo
    alert('Comment added successfully');
  } catch (error) {
    alert('Error adding comment');
  }
};

const App = () => {
  const [userId, setUserId] = useState(null);

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/register">Register</Link>
        <Link to="/login">Login</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login setUserId={setUserId} />} />
        <Route path="/dashboard" element={<Dashboard userId={userId} />} />
      </Routes>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
