// 1. Imports
import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Context for user authentication
const AuthContext = createContext();

// 2. API Service
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5327/api';

const apiService = {
  // Helper method for making API requests
  request: async (endpoint, method = 'GET', data = null, token = null) => {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers,
      credentials: 'include',
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${API_URL}${endpoint}`, config);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'An error occurred');
      }
      
      return result;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  },

  // Auth methods
  register: (userData) => apiService.request('/register', 'POST', userData),
  login: (credentials) => apiService.request('/login', 'POST', credentials),
  getProfile: (token) => apiService.request('/profile', 'GET', null, token),
  
  // Category methods
  getCategories: () => apiService.request('/categories'),
  createCategory: (categoryData, token) => apiService.request('/categories', 'POST', categoryData, token),
  
  // Post methods
  getPosts: (page = 1, perPage = 10, categoryId = null) => {
    let endpoint = `/posts?page=${page}&per_page=${perPage}`;
    if (categoryId) {
      endpoint += `&category_id=${categoryId}`;
    }
    return apiService.request(endpoint);
  },
  getPost: (postId) => apiService.request(`/posts/${postId}`),
  createPost: (postData, token) => apiService.request('/posts', 'POST', postData, token),
  updatePost: (postId, postData, token) => apiService.request(`/posts/${postId}`, 'PUT', postData, token),
  deletePost: (postId, token) => apiService.request(`/posts/${postId}`, 'DELETE', null, token),
  
  // Comment methods
  getComments: (postId) => apiService.request(`/posts/${postId}/comments`),
  addComment: (postId, commentData, token) => apiService.request(`/posts/${postId}/comments`, 'POST', commentData, token),
  deleteComment: (commentId, token) => apiService.request(`/comments/${commentId}`, 'DELETE', null, token)
};

// 3. Auth Provider Component
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  const login = useCallback(async (credentials) => {
    try {
      const result = await apiService.login(credentials);
      setUser(result.user);
      setToken(result.token);
      localStorage.setItem('token', result.token);
      return result;
    } catch (error) {
      throw error;
    }
  }, []);

  const register = useCallback(async (userData) => {
    try {
      const result = await apiService.register(userData);
      setUser(result.user);
      setToken(result.token);
      localStorage.setItem('token', result.token);
      return result;
    } catch (error) {
      throw error;
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  }, []);

  // Load user profile if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (token) {
        try {
          const { user: profile } = await apiService.getProfile(token);
          setUser(profile);
        } catch (error) {
          console.error('Failed to load user profile:', error);
          setUser(null);
          setToken(null);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    loadUser();
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isAuthenticated: !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// 4. UI Components
function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <a href="#" onClick={() => navigate('home')}>BlogApp</a>
      </div>
      
      <div className="navbar-menu-button" onClick={() => setMenuOpen(!menuOpen)}>
        <span className="material-icons">{menuOpen ? 'close' : 'menu'}</span>
      </div>
      
      <ul className={`navbar-menu ${menuOpen ? 'open' : ''}`}>
        <li><a href="#" onClick={() => navigate('home')}>Home</a></li>
        {isAuthenticated ? (
          <>
            <li><a href="#" onClick={() => navigate('new-post')}>Create Post</a></li>
            <li>
              <a href="#" className="user-menu">
                {user.username} <span className="material-icons">expand_more</span>
              </a>
              <ul className="dropdown">
                <li><a href="#" onClick={() => navigate('profile')}>Profile</a></li>
                <li><a href="#" onClick={() => navigate('my-posts')}>My Posts</a></li>
                <li><a href="#" onClick={logout}>Logout</a></li>
              </ul>
            </li>
          </>
        ) : (
          <>
            <li><a href="#" onClick={() => navigate('login')}>Login</a></li>
            <li><a href="#" onClick={() => navigate('register')}>Register</a></li>
          </>
        )}
      </ul>
    </nav>
  );
}

function Alert({ message, type = 'error', onClose }) {
  return (
    <div className={`alert ${type}`}>
      <span>{message}</span>
      {onClose && (
        <button onClick={onClose} className="close-button">
          <span className="material-icons">close</span>
        </button>
      )}
    </div>
  );
}

function Spinner() {
  return (
    <div className="spinner-container">
      <div className="spinner"></div>
    </div>
  );
}

function LoginForm() {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await login(credentials);
      navigate('home');
    } catch (error) {
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className="auth-form-container">
      <h2>Login</h2>
      {error && <Alert message={error} onClose={() => setError('')} />}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={credentials.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? <Spinner /> : 'Login'}
        </button>
      </form>
      <p className="auth-link">
        Don't have an account? <a href="#" onClick={() => navigate('register')}>Register</a>
      </p>
    </div>
  );
}

function RegisterForm() {
  const [userData, setUserData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    // Validate form
    if (userData.password !== userData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    
    try {
      await register({
        username: userData.username,
        email: userData.email,
        password: userData.password
      });
      navigate('home');
    } catch (error) {
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className="auth-form-container">
      <h2>Register</h2>
      {error && <Alert message={error} onClose={() => setError('')} />}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={userData.username}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={userData.email}
            onChange={handleChange}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={userData.password}
            onChange={handleChange}
            required
            minLength={8}
          />
        </div
