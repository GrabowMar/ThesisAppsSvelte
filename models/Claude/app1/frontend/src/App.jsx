import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API URL
const API_URL = 'http://localhost:5321';

// Main App Component
function App() {
  const [view, setView] = useState('loading'); // loading, login, register, dashboard
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check authentication status on component mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Check if user is authenticated
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_URL}/api/check-auth`, {
        method: 'GET',
        credentials: 'include',
      });
      
      const data = await response.json();
      
      if (data.authenticated) {
        setUser(data.user);
        setView('dashboard');
      } else {
        setView('login');
      }
    } catch (err) {
      console.error('Auth check error:', err);
      setView('login');
    }
  };

  // Handle user registration
  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    const username = e.target.username.value;
    const email = e.target.email.value;
    const password = e.target.password.value;
    const confirmPassword = e.target.confirmPassword.value;
    
    // Client-side validation
    if (!username || !email || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
        credentials: 'include',
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setError(data.error || 'Registration failed');
        return;
      }
      
      setSuccess('Registration successful! You can now log in.');
      setTimeout(() => {
        setView('login');
        setSuccess('');
      }, 2000);
      
    } catch (err) {
      console.error('Registration error:', err);
      setError('Registration failed. Please try again later.');
    }
  };

  // Handle user login
  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    const username = e.target.username.value;
    const password = e.target.password.value;
    
    // Client-side validation
    if (!username || !password) {
      setError('All fields are required');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setError(data.error || 'Login failed');
        return;
      }
      
      setUser(data.user);
      setView('dashboard');
      
    } catch (err) {
      console.error('Login error:', err);
      setError('Login failed. Please try again later.');
    }
  };

  // Handle user logout
  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      
      setUser(null);
      setView('login');
      
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  // Render loading view
  const renderLoading = () => (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p>Loading...</p>
    </div>
  );

  // Render login view
  const renderLogin = () => (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Login to Your Account</h2>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="username">Username or Email</label>
            <input
              type="text"
              id="username"
              name="username"
              placeholder="Enter username or email"
              autoComplete="username"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="Enter password"
              autoComplete="current-password"
            />
          </div>
          
          <button type="submit" className="btn-primary">Login</button>
        </form>
        
        <div className="auth-footer">
          <p>Don't have an account? <button onClick={() => {setView('register'); setError(''); setSuccess('');}} className="link-button">Register</button></p>
        </div>
      </div>
    </div>
  );

  // Render register view
  const renderRegister = () => (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create a New Account</h2>
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}
        
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              placeholder="Choose a username"
              autoComplete="username"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="Enter your email"
              autoComplete="email"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="Create a password"
              autoComplete="new-password"
            />
            <small>Password must be at least 8 characters with letters, numbers and special characters</small>
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              placeholder="Confirm your password"
              autoComplete="new-password"
            />
          </div>
          
          <button type="submit" className="btn-primary">Register</button>
        </form>
        
        <div className="auth-footer">
          <p>Already have an account? <button onClick={() => {setView('login'); setError(''); setSuccess('');}} className="link-button">Login</button></p>
        </div>
      </div>
    </div>
  );

  // Render dashboard view
  const renderDashboard = () => (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Welcome, {user?.username}!</h2>
        <button onClick={handleLogout} className="btn-logout">Logout</button>
      </div>
      
      <div className="dashboard-content">
        <div className="dashboard-card">
          <h3>Account Information</h3>
          <div className="user-info">
            <p><strong>Username:</strong> {user?.username}</p>
            <p><strong>Email:</strong> {user?.email}</p>
          </div>
        </div>
        
        <div className="dashboard-card">
          <h3>What's Next?</h3>
          <p>This is a sample dashboard. In a real application, you would see your content here.</p>
          <ul>
            <li>Update your profile</li>
            <li>Manage your account settings</li>
            <li>Access other features</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Main render method
  return (
    <div className="app">
      {view === 'loading' && renderLoading()}
      {view === 'login' && renderLogin()}
      {view === 'register' && renderRegister()}
      {view === 'dashboard' && renderDashboard()}
    </div>
  );
}

// Mount the app to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
