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
  
  const handle
