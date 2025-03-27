import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API URL
const API_URL = 'http://localhost:5987';

// Components
const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
          'Authorization': 'Basic ' + btoa(`${username}:${password}`),
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.token);
        onLogin(data.token);
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h2>Login</h2>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Login</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
};

const Register = ({ onRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      const data = await response.json();
      if (response.ok) {
        onRegister();
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <form onSubmit={handleRegister}>
      <h2>Register</h2>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit">Register</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
};

const PostForm = ({ token, onPostCreated }) => {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch(`${API_URL}/categories`);
        const data = await response.json();
        setCategories(data);
      } catch (error) {
        setError('Failed to fetch categories');
      }
    };
    fetchCategories();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/post`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, content, category })
      });
      const data = await response.json();
      if (response.ok) {
        onPostCreated(data.post_id);
        setTitle('');
        setContent('');
        setCategory('');
      } else {
        setError(data.message);
      }
    } catch (error) {
      setError('An error occurred. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create Post</h2>
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Title"
        required
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Content (Markdown supported)"
        required
      />
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        required
      >
        <option value="">Select Category</option>
        {categories.map((cat, index) => (
          <option key={index} value={cat}>{cat}</option>
        ))}
      </select>
      <button type="submit">Submit</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
};

const PostList = ({ posts, onPostClick }) => {
  return (
    <div>
      <h2>Posts</h2>
      {posts.map((post) => (
        <div key={post.id} onClick={() => onPostClick(post)}>
          <h3>{post.title}</h3>
          <p>Author: {post.author}</p>
          <p>Category: {post.category}</p>
        </div>
      ))}
    </div>
  );
};

const Post = ({ post, comments, onCommentSubmit, onEditClick, onDeleteClick }) => {
  const [newComment, setNewComment] = useState('');

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    await onCommentSubmit(newComment);
    setNewComment('');
  };

  return (
    <div>
      <h2>{post.title}</h2>
      <p>Author: {post.author}</p>
      <p>Category: {post.category}</p>
      <div dangerouslySetInnerHTML={{ __html: marked(post.content) }} />
      <button onClick={onEditClick}>Edit</button>
      <button onClick={onDeleteClick}>Delete</button>
      <h3>Comments</h3>
      {comments.map((comment) => (
        <div key={comment.id}>
          <p>{comment.author}: {comment.content}</p>
        </div>
      ))}
      <form onSubmit={handleCommentSubmit}>
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment"
          required
        />
        <button type="submit">Submit Comment</button>
      </form>
    </div>
  );
};

const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [view, setView] = useState('login');
  const [posts, setPosts] = useState([]);
  const [currentPost, setCurrentPost] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch(`${API_URL}/posts`);
        const data = await response.json();
        setPosts(data);
      } catch (error) {
        setError('Failed to fetch posts');
      }
    };
    fetchPosts();
  }, []);

  const handleLogin = (newToken) => {
    setToken(newToken);
    setView('home');
  };

  const handleRegister = () => {
    setView('login');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setView('login');
  };

  const handlePostCreated = async (postId) => {
    try {
      const response = await fetch(`${API_URL}/post/${postId}`);
      const data = await response.json();
      setPosts([...posts, data]);
    } catch (error) {
      setError('Failed to fetch new post');
    }
  };

  const handlePostClick = async (post) => {
    try {
      const response = await fetch(`${API_URL}/post/${post.id}`);
      const data = await response.json();
      setCurrentPost(data);
      setView('post');
    } catch (error) {
      setError('Failed to fetch post details');
    }
  };

  const handleCommentSubmit = async (content) => {
    try {
      await fetch(`${API_URL}/post/${currentPost.id}/comment`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
      });
      const response = await fetch(`${API_URL}/post/${currentPost.id}`);
      const data = await response.json();
      setCurrentPost(data);
    } catch (error) {
      setError('Failed to submit comment');
    }
  };

  const handleEditPost = async () => {
    setView('editPost');
  };

  const handleDeletePost = async () => {
    try {
      await fetch(`${API_URL}/post/${currentPost.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setPosts(posts.filter(post => post.id !== currentPost.id));
      setCurrentPost(null);
      setView('home');
    } catch (error) {
      setError('Failed to delete post');
    }
  };

  const handleUpdatePost = async (title, content, category) => {
    try {
      await fetch(`${API_URL}/post/${currentPost.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title, content, category })
      });
      const response = await fetch(`${API_URL}/post/${currentPost.id}`);
      const data = await response.json();
      setCurrentPost(data);
      setPosts(posts.map(post => post.id === currentPost.id ? data : post));
      setView('post');
    } catch (error) {
      setError('Failed to update post');
    }
  };

  const renderView = () => {
    switch (view) {
      case 'login':
        return <Login onLogin={handleLogin} />;
      case 'register':
        return <Register onRegister={handleRegister} />;
      case 'home':
        return (
          <>
            <button onClick={() => setView('createPost')}>Create Post</button>
            <button onClick={handleLogout}>Logout</button>
            <PostList posts={posts} onPostClick={handlePostClick} />
          </>
        );
      case 'createPost':
        return (
          <>
            <button onClick={() => setView('home')}>Back</button>
            <PostForm token={token} onPostCreated={handlePostCreated} />
          </>
        );
      case 'post':
        return currentPost ? (
          <>
            <button onClick={() => setView('home')}>Back</button>
            <Post
              post={currentPost}
              comments={currentPost.comments}
              onCommentSubmit={handleCommentSubmit}
              onEditClick={handleEditPost}
              onDeleteClick={handleDeletePost}
            />
          </>
        ) : null;
      case 'editPost':
        return currentPost ? (
          <>
            <button onClick={() => setView('post')}>Back</button>
            <PostForm
              token={token}
              initialTitle={currentPost.title}
              initialContent={currentPost.content}
              initialCategory={currentPost.category}
              onSubmit={handleUpdatePost}
            />
          </>
        ) : null;
      default:
        return null;
    }
  };

  return (
    <div className="app">
      {error && <p className="error">{error}</p>}
      {renderView()}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
