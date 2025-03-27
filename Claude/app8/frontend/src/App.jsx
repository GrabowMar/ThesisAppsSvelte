import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './App.css';

// API base URL
const API_URL = 'http://localhost:5335/api';

// Set up axios with JWT token if available
const setupAxios = () => {
  const token = localStorage.getItem('token');
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Authentication Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      setupAxios();
      const token = localStorage.getItem('token');
      
      if (token) {
        try {
          const response = await axios.get(`${API_URL}/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Authentication error:', error);
          localStorage.removeItem('token');
        }
      }
      
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (credentials) => {
    try {
      const response = await axios.post(`${API_URL}/login`, credentials);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      setupAxios();
      setUser(user);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.error || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/register`, userData);
      const { user, token } = response.data;
      
      localStorage.setItem('token', token);
      setupAxios();
      setUser(user);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.error || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// App Component
const App = () => {
  const [page, setPage] = useState('home');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedThread, setSelectedThread] = useState(null);
  
  const navigateTo = (newPage, data = null) => {
    if (newPage === 'category' && data) {
      setSelectedCategory(data);
    } else if (newPage === 'thread' && data) {
      setSelectedThread(data);
    } else if (newPage === 'home') {
      setSelectedCategory(null);
      setSelectedThread(null);
    }
    
    setPage(newPage);
    window.scrollTo(0, 0);
  };
  
  // Render current page based on state
  const renderContent = () => {
    switch (page) {
      case 'home':
        return <HomePage navigateTo={navigateTo} />;
      case 'category':
        return <CategoryPage 
                 category={selectedCategory} 
                 navigateTo={navigateTo} 
               />;
      case 'thread':
        return <ThreadPage 
                 threadId={selectedThread} 
                 navigateTo={navigateTo} 
               />;
      case 'create-thread':
        return <CreateThreadPage navigateTo={navigateTo} />;
      case 'login':
        return <LoginPage navigateTo={navigateTo} />;
      case 'register':
        return <RegisterPage navigateTo={navigateTo} />;
      default:
        return <HomePage navigateTo={navigateTo} />;
    }
  };
  
  return (
    <AuthProvider>
      <div className="app">
        <Navbar navigateTo={navigateTo} />
        <main className="container">
          {renderContent()}
        </main>
        <Footer />
      </div>
    </AuthProvider>
  );
};

// Navbar Component
const Navbar = ({ navigateTo }) => {
  const { user, logout } = React.useContext(AuthContext);
  
  return (
    <header className="navbar">
      <div className="container navbar-container">
        <div className="logo" onClick={() => navigateTo('home')}>
          Forum App
        </div>
        
        <nav>
          <button className="nav-link" onClick={() => navigateTo('home')}>Home</button>
          {user ? (
            <>
              <button 
                className="nav-link" 
                onClick={() => navigateTo('create-thread')}
              >
                Create Thread
              </button>
              <span className="user-welcome">Hello, {user.username}</span>
              <button className="btn btn-outline" onClick={logout}>Logout</button>
            </>
          ) : (
            <>
              <button className="btn btn-outline" onClick={() => navigateTo('login')}>
                Login
              </button>
              <button className="btn btn-primary" onClick={() => navigateTo('register')}>
                Register
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="footer">
      <div className="container">
        <p>&copy; {new Date().getFullYear()} Forum App. All rights reserved.</p>
      </div>
    </footer>
  );
};

// Home Page Component
const HomePage = ({ navigateTo }) => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API_URL}/categories`);
        setCategories(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch categories');
        setLoading(false);
        console.error('Error fetching categories:', err);
      }
    };
    
    fetchCategories();
  }, []);
  
  if (loading) return <LoadingSpinner />;
  
  if (error) return <ErrorMessage message={error} />;
  
  return (
    <div className="home-page">
      <div className="hero-section">
        <h1>Welcome to our Forum Community</h1>
        <p>Join discussions, share your thoughts, and connect with others.</p>
      </div>
      
      <h2>Categories</h2>
      <div className="categories-grid">
        {categories.map(category => (
          <div 
            key={category.id} 
            className="category-card"
            onClick={() => navigateTo('category', category)}
          >
            <h3>{category.name}</h3>
            <p>{category.description}</p>
            <span className="thread-count">
              {category.thread_count} {category.thread_count === 1 ? 'thread' : 'threads'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Category Page Component
const CategoryPage = ({ category, navigateTo }) => {
  const [threads, setThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sort, setSort] = useState('new');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  useEffect(() => {
    const fetchThreads = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `${API_URL}/threads?category=${category.id}&sort=${sort}&search=${searchTerm}&page=${page}`
        );
        setThreads(response.data.threads);
        setTotalPages(response.data.pages);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch threads');
        setLoading(false);
        console.error('Error fetching threads:', err);
      }
    };
    
    fetchThreads();
  }, [category.id, sort, searchTerm, page]);
  
  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1); // Reset to first page on new search
  };
  
  if (!category) {
    navigateTo('home');
    return null;
  }
  
  return (
    <div className="category-page">
      <div className="category-header">
        <div>
          <h1>{category.name}</h1>
          <p>{category.description}</p>
        </div>
        <div className="category-actions">
          <button 
            className="btn btn-primary" 
            onClick={() => navigateTo('create-thread')}
          >
            Create Thread
          </button>
        </div>
      </div>
      
      <div className="filters-bar">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search threads..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit" className="btn">Search</button>
        </form>
        
        <div className="sort-options">
          <label>Sort by:</label>
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="new">Newest</option>
            <option value="comments">Most Comments</option>
            <option value="top">Most Viewed</option>
          </select>
        </div>
      </div>
      
      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : threads.length === 0 ? (
        <div className="no-results">
          <p>No threads found{searchTerm ? ` for "${searchTerm}"` : ''}.</p>
        </div>
      ) : (
        <>
          <div className="threads-list">
            {threads.map(thread => (
              <div 
                key={thread.id} 
                className="thread-item"
                onClick={() => navigateTo('thread', thread.id)}
              >
                <h3>{thread.title}</h3>
                <div className="thread-meta">
                  <span>By {thread.author.username}</span>
                  <span>{formatDate(thread.created_at)}</span>
                  <span>{thread.comment_count} comments</span>
                  <span>{thread.views} views</span>
                </div>
                <p className="thread-preview">
                  {thread.content.length > 150 
                    ? thread.content.substring(0, 150) + '...' 
                    : thread.content}
                </p>
              </div>
            ))}
          </div>
          
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn"
              >
                Previous
              </button>
              <span>{page} of {totalPages}</span>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="btn"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

// Thread Page Component
const ThreadPage = ({ threadId, navigateTo }) => {
  const { user } = React.useContext(AuthContext);
  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [editingComment, setEditingComment] = useState(null);
  
  useEffect(() => {
    const fetchThread = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/threads/${threadId}`);
        setThread(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch thread');
        setLoading(false);
        console.error('Error fetching thread:', err);
      }
    };
    
    if (threadId) {
      fetchThread();
    }
  }, [threadId]);
  
  const handleSubmitComment = async (e) => {
    e.preventDefault();
    
    if (!commentText.trim()) return;
    
    if (!user) {
      navigateTo('login');
      return;
    }
    
    try {
      setSubmitting(true);
      
      if (editingComment) {
        // Update existing comment
        await axios.put(
          `${API_URL}/comments/${editingComment.id}`, 
          { content: commentText }
        );
        
        // Update comment in the UI
        setThread(prevThread => ({
          ...prevThread,
          comments: prevThread.comments.map(comment => 
            comment.id === editingComment.id 
              ? { ...comment, content: commentText, updated_at: new Date().toISOString() } 
              : comment
          )
        }));
        
        setEditingComment(null);
      } else {
        // Create new comment
        const response = await axios.post(
          `${API_URL}/threads/${threadId}/comments`, 
          { content: commentText }
        );
        
        // Add new comment to the UI
        setThread(prevThread => ({
          ...prevThread,
          comments: [...prevThread.comments, response.data.comment]
        }));
      }
      
      setCommentText('');
      setSubmitting(false);
    } catch (err) {
      console.error('Error with comment:', err);
      setSubmitting(false);
    }
  };
  
  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/comments/${commentId}`);
      
      // Remove comment from the UI
      setThread(prevThread => ({
        ...prevThread,
        comments: prevThread.comments.filter(comment => comment.id !== commentId)
      }));
    } catch (err) {
      console.error('Error deleting comment:', err);
      alert('Failed to delete comment');
    }
  };
  
  const handleEditComment = (comment) => {
    setEditingComment(comment);
    setCommentText(comment.content);
    
    // Scroll to comment form
    document.getElementById('comment-form').scrollIntoView({ behavior: 'smooth' });
  };
  
  const handleDeleteThread = async () => {
    if (!window.confirm('Are you sure you want to delete this thread?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/threads/${threadId}`);
      navigateTo('home');
    } catch (err) {
      console.error('Error deleting thread:', err);
      alert('Failed to delete thread');
    }
  };
  
  if (loading) return <LoadingSpinner />;
  
  if (error || !thread) return <ErrorMessage message={error || 'Thread not found'} />;
  
  return (
    <div className="thread-page">
      <div className="thread-header">
        <div className="breadcrumbs">
          <span onClick={() => navigateTo('home')}>Home</span> &gt;
          <span onClick={() => navigateTo('category', { id: thread.category_id, name: thread.category_name })}>
            {thread.category_name}
          </span>
        </div>
        
        <h1>{thread.title}</h1>
        
        <div className="thread-meta">
          <div>
            <span>Posted by {thread.author.username}</span>
            <span>{formatDate(thread.created_at)}</span>
            <span>{thread.views} views</span>
          </div>
          
          {user && user.id === thread.author.id && (
            <div className="thread-actions">
              <button className="btn btn-danger" onClick={handleDeleteThread}>
                Delete Thread
              </button>
            </div>
          )}
        </div>
      </div>
      
      <div className="thread-content">
        {thread.content.split('\n').map((paragraph, i) => (
          <p key={i}>{paragraph}</p>
        ))}
      </div>
      
      <div className="comments-section">
        <h2>{thread.comments.length} {thread.comments.length === 1 ? 'Comment' : 'Comments'}</h2>
        
        {thread.comments.length === 0 ? (
          <p className="no-comments">No comments yet. Be the first to comment.</p>
        ) : (
          <div className="comments-list">
            {thread.comments.map(comment => (
              <div key={comment.id} className="comment-item">
                <div className="comment-header">
                  <div className="comment-author">
                    <span>{comment.author.username}</span>
                    <span className="comment-date">{formatDate(comment.created_at)}</span>
                    {comment.updated_at !== comment.created_at && (
                      <span className="comment-edited">(edited)</span>
                    )}
                  </div>
                  
                  {user && user.id === comment.author.id && (
                    <div className="comment-actions">
                      <button 
                        className="btn-link" 
                        onClick={() => handleEditComment(comment)}
                      >
                        Edit
                      </button>
                      <button 
                        className="btn-link text-danger" 
                        onClick={() => handleDeleteComment(comment.id)}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
                
                <div className="comment-content">
                  {comment.content.split('\n').map((paragraph, i) => (
                    <p key={i}>{paragraph}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        
        <div className="comment-form-container" id="comment-form">
          <h3>{editingComment ? 'Edit Comment' : 'Add a Comment'}</h3>
          
          {!user ? (
            <div className="login-prompt">
              <p>Please <button className="btn-link" onClick={() => navigateTo('login')}>login</button> to add a comment.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmitComment} className="comment-form">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Write your comment..."
                required
                rows={4}
              />
              
              <div className="form-actions">
                {editingComment && (
                  <button 
                    type="button" 
                    className="btn btn-outline" 
                    onClick={() => {
                      setEditingComment(null);
                      setCommentText('');
                    }}
                  >
                    Cancel
                  </button>
                )}
                
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={submitting || !commentText.trim()}
                >
                  {submitting ? 'Submitting...' : editingComment ? 'Update Comment' : 'Post Comment'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

// Create Thread Page Component
const CreateThreadPage = ({ navigateTo }) => {
  const { user } = React.useContext(AuthContext);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  useEffect(() => {
    // Redirect if not logged in
    if (!user && !loading) {
      navigateTo('login');
      return;
    }
    
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API_URL}/categories`);
        setCategories(response.data);
        if (response.data.length > 0) {
          setCategoryId(response.data[0].id.toString());
        }
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch categories');
        setLoading(false);
        console.error('Error fetching categories:', err);
      }
    };
    
    fetchCategories();
  }, [user, loading, navigateTo]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!title.trim() || !content.trim() || !categoryId) {
      return;
    }
    
    try {
      setSubmitting(true);
      const response = await axios.post(`${API_URL}/threads`, {
        title,
        content,
        category_id: parseInt(categoryId)
      });
      
      setSubmitting(false);
      navigateTo('thread', response.data.thread.id);
    } catch (err) {
      console.error('Error creating thread:', err);
      setError('Failed to create thread');
      setSubmitting(false);
    }
  };
  
  if (loading) return <LoadingSpinner />;
  
  if (error) return <ErrorMessage message={error} />;
  
  return (
    <div className="create-thread-page">
      <h1>Create New Thread</h1>
      
      <form onSubmit={handleSubmit} className="thread-form">
        <div className="form-group">
          <label htmlFor="category">Category</label>
          <select 
            id="category" 
            value={categoryId} 
            onChange={(e) => setCategoryId(e.target.value)}
            required
          >
            <option value="">Select a category</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="title">Title</label>
          <input 
            type="text" 
            id="title" 
            value={title} 
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Thread title"
            required
            maxLength={100}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="content">Content</label>
          <textarea 
            id="content" 
            value={content} 
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write your post content here..."
            required
            rows={10}
          />
        </div>
        
        <div className="form-actions">
          <button 
            type="button" 
            className="btn btn-outline" 
            onClick={() => navigateTo('home')}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={submitting || !title.trim() || !content.trim() || !categoryId}
          >
            {submitting ? 'Creating...' : 'Create Thread'}
          </button>
        </div>
      </form>
    </div>
  );
};

// Login Page Component
const LoginPage = ({ navigateTo }) => {
  const { login, user, loading } = React.useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Redirect if already logged in
  useEffect(() => {
    if (user && !loading) {
      navigateTo('home');
    }
  }, [user, loading, navigateTo]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    if (!username.trim() || !password.trim()) {
      return;
    }
    
    try {
      setSubmitting(true);
      const result = await login({ username, password });
      
      if (result.success) {
        navigateTo('home');
      } else {
        setError(result.message);
      }
      
      setSubmitting(false);
    } catch (err) {
      console.error('Login error:', err);
      setError('An unexpected error occurred');
      setSubmitting(false);
    }
  };
  
  if (loading || user) return <LoadingSpinner />;
  
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Login</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input 
              type="text" 
              id="username" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary btn-block" 
            disabled={submitting}
          >
            {submitting ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <p className="auth-redirect">
          Don't have an account?{' '}
          <button className="btn-link" onClick={() => navigateTo('register')}>
            Register
          </button>
        </p>
      </div>
    </div>
  );
};

// Register Page Component
const RegisterPage = ({ navigateTo }) => {
  const { register, user, loading } = React.useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  // Redirect if already logged in
  useEffect(() => {
    if (user && !loading) {
      navigateTo('home');
    }
  }, [user, loading, navigateTo]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    if (!username.trim() || !password.trim()) {
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      setSubmitting(true);
      const result = await register({ username, password });
      
      if (result.success) {
        navigateTo('home');
      } else {
        setError(result.message);
      }
      
      setSubmitting(false);
    } catch (err) {
      console.error('Registration error:', err);
      setError('An unexpected error occurred');
      setSubmitting(false);
    }
  };
  
  if (loading || user) return <LoadingSpinner />;
  
  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Register</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input 
              type="text" 
              id="username" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={50}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input 
              type="password" 
              id="confirmPassword" 
              value={confirmPassword} 
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary btn-block" 
            disabled={submitting}
          >
            {submitting ? 'Registering...' : 'Register'}
          </button>
        </form>
        
        <p className="auth-redirect">
          Already have an account?{' '}
          <button className="btn-link" onClick={() => navigateTo('login')}>
            Login
          </button>
        </p>
      </div>
    </div>
  );
};

// Utility Components
const LoadingSpinner = () => (
  <div className="loading-spinner">
    <div className="spinner"></div>
    <p>Loading...</p>
  </div>
);

const ErrorMessage = ({ message }) => (
  <div className="error-container">
    <h2>Error</h2>
    <p>{message || 'Something went wrong.'}</p>
    <button className="btn" onClick={() => window.location.reload()}>
      Try Again
    </button>
  </div>
);

// Helper Functions
const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  }
};

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;


