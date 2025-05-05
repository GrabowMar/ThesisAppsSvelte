/*
App.jsx – Frontend for Blog Application (React)
Ports: 5647 (frontend)
Features:
 - Multipage routing (login, register, dashboard, create/edit post, view post).
 - API calls to the Flask backend.
 - Error and loading states.
 - Markdown support for previewing post content.
 - Mounting logic using ReactDOM.
*/

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Define different views
const VIEWS = {
  LOGIN: 'LOGIN',
  REGISTER: 'REGISTER',
  DASHBOARD: 'DASHBOARD',
  CREATE_POST: 'CREATE_POST',
  VIEW_POST: 'VIEW_POST',
  EDIT_POST: 'EDIT_POST'
};

function App() {
  // Global state
  const [view, setView] = useState(VIEWS.LOGIN);
  const [currentUser, setCurrentUser] = useState(null); // username
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null); // Object with post details
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // API URL (adjust if needed)
  const API_URL = '/api';

  // Fetch posts from API
  const fetchPosts = async () => {
    try {
      setLoading(true);
      const res = await fetch(API_URL + '/posts');
      const data = await res.json();
      if (res.ok) setPosts(data);
      else setError(data.error || "Error fetching posts.");
    } catch (err) {
      setError("Error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Switch to Dashboard view once logged in
  useEffect(() => {
    if (view === VIEWS.DASHBOARD) {
      fetchPosts();
    }
  }, [view]);

  // Common Function - handle error clearing
  const clearError = () => {
    setError('');
  };

  // Login form submit handler
  const handleLogin = async (e) => {
    e.preventDefault();
    clearError();
    const { username, password } = e.target.elements;
    try {
      setLoading(true);
      const res = await fetch(API_URL + '/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username: username.value, password: password.value })
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentUser(data.username);
        setView(VIEWS.DASHBOARD);
      } else {
        setError(data.error || "Login failed");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Registration form submit handler
  const handleRegister = async (e) => {
    e.preventDefault();
    clearError();
    const { username, password } = e.target.elements;
    try {
      setLoading(true);
      const res = await fetch(API_URL + '/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: username.value, password: password.value})
      });
      const data = await res.json();
      if (res.ok) {
        alert("Registration successful. Please log in.");
        setView(VIEWS.LOGIN);
      } else {
        setError(data.error || "Registration failed");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Create Post form handler
  const handleCreatePost = async (e) => {
    e.preventDefault();
    clearError();
    const { title, content } = e.target.elements;
    try {
      setLoading(true);
      const res = await fetch(API_URL + '/posts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          author: currentUser,
          title: title.value,
          content: content.value
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert("Post created successfully.");
        setView(VIEWS.DASHBOARD);
      } else {
        setError(data.error || "Failed to create post");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // View Post details (with markdown preview)
  const handleViewPost = async (postId) => {
    clearError();
    try {
      setLoading(true);
      const res = await fetch(API_URL + `/posts/${postId}`);
      const data = await res.json();
      if (res.ok) {
        setSelectedPost(data);
        setView(VIEWS.VIEW_POST);
      } else {
        setError(data.error || "Unable to fetch post");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Edit Post form handler (reuses create API with PUT method)
  const handleEditPost = async (e) => {
    e.preventDefault();
    clearError();
    const { title, content } = e.target.elements;
    try {
      setLoading(true);
      const res = await fetch(API_URL + `/posts/${selectedPost.id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          author: currentUser,
          title: title.value,
          content: content.value
        })
      });
      const data = await res.json();
      if (res.ok) {
        alert("Post updated successfully.");
        setView(VIEWS.DASHBOARD);
        fetchPosts();
      } else {
        setError(data.error || "Unable to update post");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Render loading, error and navigation controls
  return (
    <div className="app-container">
      <header>
        <h1>Flask + React Blog</h1>
        {currentUser && (
          <div className="nav-buttons">
            <button onClick={() => {setView(VIEWS.DASHBOARD); clearError();}}>Dashboard</button>
            <button onClick={() => {setView(VIEWS.CREATE_POST); clearError();}}>New Post</button>
            <button onClick={() => {setCurrentUser(null); setView(VIEWS.LOGIN); clearError();}}>Logout</button>
          </div>
        )}
      </header>
      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">Error: {error}</div>}
      <main>
        {view === VIEWS.LOGIN && (
          <div className="form-container">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
              <input type="text" name="username" placeholder="Username" required />
              <input type="password" name="password" placeholder="Password" required />
              <button type="submit">Login</button>
            </form>
            <p>
              Don't have an account?{" "}
              <span className="link" onClick={() => {setView(VIEWS.REGISTER); clearError();}}>
                Register here
              </span>
            </p>
          </div>
        )}

        {view === VIEWS.REGISTER && (
          <div className="form-container">
            <h2>Register</h2>
            <form onSubmit={handleRegister}>
              <input type="text" name="username" placeholder="Username" required />
              <input type="password" name="password" placeholder="Password" required />
              <button type="submit">Register</button>
            </form>
            <p>
              Already have an account?{" "}
              <span className="link" onClick={() => {setView(VIEWS.LOGIN); clearError();}}>
                Login here
              </span>
            </p>
          </div>
        )}

        {view === VIEWS.DASHBOARD && (
          <div>
            <h2>Dashboard</h2>
            {posts.length === 0 ? (
              <p>No posts available. Create one now!</p>
            ) : (
              <ul className="post-list">
                {posts.map((post) => (
                  <li key={post.id}>
                    <h3>{post.title}</h3>
                    <p>
                      <em>By {post.author} on {new Date(post.created).toLocaleString()}</em>
                    </p>
                    <button onClick={() => handleViewPost(post.id)}>View</button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {view === VIEWS.CREATE_POST && (
          <div className="form-container">
            <h2>Create New Post</h2>
            <form onSubmit={handleCreatePost}>
              <input type="text" name="title" placeholder="Post Title" required />
              <textarea name="content" placeholder="Write your post in Markdown..." required></textarea>
              <button type="submit">Publish</button>
            </form>
          </div>
        )}

        {view === VIEWS.VIEW_POST && selectedPost && (
          <div className="post-detail">
            <h2>{selectedPost.title}</h2>
            <p>
              <em>By {selectedPost.author} on {new Date(selectedPost.created).toLocaleString()}</em>
            </p>
            <div className="post-content">
              <ReactMarkdown>{selectedPost.content}</ReactMarkdown>
            </div>
            <div>
              <button onClick={() => {setView(VIEWS.EDIT_POST); clearError();}}>Edit Post</button>
              <button onClick={() => setView(VIEWS.DASHBOARD)}>Back</button>
            </div>
            <div className="comments-section">
              <h3>Comments</h3>
              {selectedPost.comments.length === 0 ? (
                <p>No comments yet.</p>
              ) : (
                <ul>
                  {selectedPost.comments.map((comment, idx) => (
                    <li key={idx}>
                      <strong>{comment.author}</strong>: {comment.content}
                      <br />
                      <small>{new Date(comment.created).toLocaleString()}</small>
                    </li>
                  ))}
                </ul>
              )}
              {/* For brevity, we do not implement comment creation form here.
                  (Can be added similarly via a POST fetch call to /posts/:post_id/comments) */}
            </div>
          </div>
        )}

        {view === VIEWS.EDIT_POST && selectedPost && (
          <div className="form-container">
            <h2>Edit Post</h2>
            <form onSubmit={handleEditPost}>
              <input type="text" name="title" defaultValue={selectedPost.title} required />
              <textarea name="content" defaultValue={selectedPost.content} required></textarea>
              <button type="submit">Update Post</button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

// Mounting logic: attach the App component to the DOM element with id "root"
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
