import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [currentView, setCurrentView] = useState('home'); // home, login, register, createPost, editPost, postDetails
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [newPost, setNewPost] = useState({ title: '', content: '', category: '' });
  const [loginError, setLoginError] = useState('');
  const [registerError, setRegisterError] = useState('');
  const [postError, setPostError] = useState('');
  const [commentText, setCommentText] = useState('');

  useEffect(() => {
    checkLoginStatus();
    fetchPosts();
  }, []);

  const checkLoginStatus = async () => {
    try {
      const response = await fetch('/api/is_logged_in');
      const data = await response.json();
      setIsLoggedIn(data.isLoggedIn);
      if (data.isLoggedIn) {
        setUsername(data.username);
      }
    } catch (error) {
      console.error('Error checking login status:', error);
    }
  };

  const fetchPosts = async () => {
    try {
      const response = await fetch('/api/posts');
      const data = await response.json();
      setPosts(data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };


  // Authentication Handlers
  const handleRegister = async (e) => {
    e.preventDefault();
    setRegisterError('');
    const username = e.target.username.value;
    const password = e.target.password.value;

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        setCurrentView('login');
      } else {
        const errorData = await response.json();
        setRegisterError(errorData.message || 'Registration failed');
      }
    } catch (error) {
      console.error('Error registering:', error);
      setRegisterError('An unexpected error occurred.');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    const username = e.target.username.value;
    const password = e.target.password.value;

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        setIsLoggedIn(true);
        setUsername(username);
        setCurrentView('home');
        fetchPosts();
      } else {
        const errorData = await response.json();
        setLoginError(errorData.message || 'Login failed');
      }
    } catch (error) {
      console.error('Error logging in:', error);
      setLoginError('An unexpected error occurred.');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', { method: 'POST' });
      setIsLoggedIn(false);
      setUsername('');
      setCurrentView('home');
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };


  // Post Management Handlers
  const handleCreatePost = async (e) => {
    e.preventDefault();
    setPostError('');

    try {
      const response = await fetch('/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPost),
      });

      if (response.ok) {
        fetchPosts();
        setCurrentView('home');
        setNewPost({ title: '', content: '', category: '' });
      } else {
        const errorData = await response.json();
        setPostError(errorData.message || 'Post creation failed');
      }
    } catch (error) {
      console.error('Error creating post:', error);
      setPostError('An unexpected error occurred.');
    }
  };

  const handleEditPost = async (e) => {
    e.preventDefault();
    setPostError('');

    try {
      const response = await fetch(`/api/posts/${selectedPost.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedPost),
      });

      if (response.ok) {
        fetchPosts();
        setCurrentView('home');
        setSelectedPost(null);
      } else {
        const errorData = await response.json();
        setPostError(errorData.message || 'Post update failed');
      }
    } catch (error) {
      console.error('Error updating post:', error);
      setPostError('An unexpected error occurred.');
    }
  };

  const handleDeletePost = async (postId) => {
    try {
      const response = await fetch(`/api/posts/${postId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchPosts();
      } else {
        console.error('Error deleting post');
      }
    } catch (error) {
      console.error('Error deleting post:', error);
    }
  };

  const handleAddComment = async (postId) => {
    try {
      const response = await fetch(`/api/posts/${postId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: commentText }),
      });

      if (response.ok) {
        setCommentText('');
        fetchPosts(); // Refresh posts to see new comment
        setSelectedPost(posts.find(post => post.id === postId)); // Refresh selected post
      } else {
        console.error('Error adding comment');
      }
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };


  // View Rendering Functions
  const renderHomePage = () => (
    <div>
      <h2>Blog Posts</h2>
      {posts.map((post) => (
        <div key={post.id} className="post-card">
          <h3>{post.title}</h3>
          <p>Author: {post.author}</p>
          <p>Category: {post.category}</p>
          <p>{post.content.substring(0, 100)}...</p>
          <button onClick={() => {
            setSelectedPost(post);
            setCurrentView('postDetails');
          }}>Read More</button>
          {isLoggedIn && post.author === username && (
            <>
              <button onClick={() => {
                setSelectedPost({...post}); // Create a copy to avoid direct mutation
                setCurrentView('editPost');
              }}>Edit</button>
              <button onClick={() => handleDeletePost(post.id)}>Delete</button>
            </>
          )}
        </div>
      ))}
      {isLoggedIn && (
        <button onClick={() => setCurrentView('createPost')}>Create New Post</button>
      )}
    </div>
  );

  const renderPostDetails = () => {
    if (!selectedPost) return <div>Loading...</div>;

    return (
      <div>
        <h2>{selectedPost.title}</h2>
        <p>Author: {selectedPost.author}</p>
        <p>Category: {selectedPost.category}</p>
        <p>{selectedPost.content}</p>

        <h3>Comments</h3>
        {selectedPost.comments && selectedPost.comments.map((comment, index) => (
          <div key={index} className="comment">
            <p>{comment.author}: {comment.text}</p>
          </div>
        ))}

        {isLoggedIn && (
          <div className="add-comment">
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Add a comment..."
            />
            <button onClick={() => handleAddComment(selectedPost.id)}>Post Comment</button>
          </div>
        )}

        <button onClick={() => setCurrentView('home')}>Back to Home</button>
      </div>
    );
  };

  const renderLoginView = () => (
    <form onSubmit={handleLogin} className="auth-form">
      <h2>Login</h2>
      {loginError && <p className="error">{loginError}</p>}
      <input type="text" name="username" placeholder="Username" required />
      <input type="password" name="password" placeholder="Password" required />
      <button type="submit">Login</button>
      <button type="button" onClick={() => setCurrentView('register')}>Register</button>
    </form>
  );

  const renderRegisterView = () => (
    <form onSubmit={handleRegister} className="auth-form">
      <h2>Register</h2>
      {registerError && <p className="error">{registerError}</p>}
      <input type="text" name="username" placeholder="Username" required />
      <input type="password" name="password" placeholder="Password" required />
      <button type="submit">Register</button>
      <button type="button" onClick={() => setCurrentView('login')}>Login</button>
    </form>
  );

  const renderCreatePostView = () => (
    <form onSubmit={handleCreatePost} className="post-form">
      <h2>Create New Post</h2>
      {postError && <p className="error">{postError}</p>}
      <input
        type="text"
        placeholder="Title"
        value={newPost.title}
        onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
        required
      />
      <textarea
        placeholder="Content"
        value={newPost.content}
        onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
        required
      />
      <input
        type="text"
        placeholder="Category"
        value={newPost.category}
        onChange={(e) => setNewPost({ ...newPost, category: e.target.value })}
      />
      <button type="submit">Create Post</button>
      <button type="button" onClick={() => setCurrentView('home')}>Cancel</button>
    </form>
  );

  const renderEditPostView = () => {
    if (!selectedPost) return <div>Loading...</div>;

    return (
      <form onSubmit={handleEditPost} className="post-form">
        <h2>Edit Post</h2>
        {postError && <p className="error">{postError}</p>}
        <input
          type="text"
          placeholder="Title"
          value={selectedPost.title}
          onChange={(e) => setSelectedPost({ ...selectedPost, title: e.target.value })}
          required
        />
        <textarea
          placeholder="Content"
          value={selectedPost.content}
          onChange={(e) => setSelectedPost({ ...selectedPost, content: e.target.value })}
          required
        />
        <input
          type="text"
          placeholder="Category"
          value={selectedPost.category}
          onChange={(e) => setSelectedPost({ ...selectedPost, category: e.target.value })}
        />
        <button type="submit">Update Post</button>
        <button type="button" onClick={() => setCurrentView('home')}>Cancel</button>
      </form>
    );
  };


  // Main Render Logic
  return (
    <div className="app-container">
      <header>
        <h1>Simple Blog</h1>
        <nav>
          {isLoggedIn ? (
            <>
              <span>Welcome, {username}!</span>
              <button onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <button onClick={() => setCurrentView('login')}>Login</button>
              <button onClick={() => setCurrentView('register')}>Register</button>
            </>
          )}
        </nav>
      </header>

      <main>
        {currentView === 'home' && renderHomePage()}
        {currentView === 'login' && renderLoginView()}
        {currentView === 'register' && renderRegisterView()}
        {currentView === 'createPost' && renderCreatePostView()}
        {currentView === 'editPost' && renderEditPostView()}
        {currentView === 'postDetails' && renderPostDetails()}
      </main>

      <footer>
        <p>&copy; 2024 Simple Blog</p>
      </footer>
    </div>
  );
}


// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
