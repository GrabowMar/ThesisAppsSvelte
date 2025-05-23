// 1. Imports
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// 2. Main App Component
function App() {
  // 3. State Management
  const [currentView, setCurrentView] = useState('login');
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Login form state
  const [loginForm, setLoginForm] = useState({
    username: '',
    password: ''
  });

  // Register form state
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  // Form validation errors
  const [loginErrors, setLoginErrors] = useState({});
  const [registerErrors, setRegisterErrors] = useState({});
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);

  // 4. Lifecycle Functions
  useEffect(() => {
    // Check if user is already authenticated when the app loads
    checkAuthStatus();
  }, []);

  useEffect(() => {
    // Fetch dashboard data when authenticated and on dashboard view
    if (isAuthenticated && currentView === 'dashboard') {
      fetchDashboardData();
    }
  }, [isAuthenticated, currentView]);

  // 5. Event Handlers
  const handleLoginInputChange = (e) => {
    const { name, value } = e.target;
    setLoginForm({
      ...loginForm,
      [name]: value
    });
    
    // Clear specific error when user starts typing
    if (loginErrors[name]) {
      setLoginErrors({
        ...loginErrors,
        [name]: ''
      });
    }
  };

  const handleRegisterInputChange = (e) => {
    const { name, value } = e.target;
    setRegisterForm({
      ...registerForm,
      [name]: value
    });
    
    // Clear specific error when user starts typing
    if (registerErrors[name]) {
      setRegisterErrors({
        ...registerErrors,
        [name]: ''
      });
    }
  };

  const handleViewChange = (view) => {
    setCurrentView(view);
    setError(null); // Clear any previous errors
  };

  const validateLoginForm = () => {
    const errors = {};
    
    if (!loginForm.username.trim()) {
      errors.username = 'Username or email is required';
    }
    
    if (!loginForm.password) {
      errors.password = 'Password is required';
    }
    
    setLoginErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateRegisterForm = () => {
    const errors = {};
    
    if (!registerForm.username.trim()) {
      errors.username = 'Username is required';
    } else if (registerForm.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }
    
    if (!registerForm.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(registerForm.email)) {
      errors.email = 'Email is invalid';
    }
    
    if (!registerForm.password) {
      errors.password = 'Password is required';
    } else if (registerForm.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(registerForm.password)) {
      errors.password = 'Password must contain uppercase, lowercase, and a number';
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setRegisterErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateLoginForm()) {
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      const userData = await loginUser(loginForm);
      
      setUser(userData);
      setIsAuthenticated(true);
      setCurrentView('dashboard');
      
      // Reset form
      setLoginForm({ username: '', password: '' });
    } catch (err) {
      setError(err.message || 'Failed to login. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!validateRegisterForm()) {
      return;
    }
    
    try {
      setIsLoading(true);
      setError(null);
      
      await registerUser(registerForm);
      
      // Automatically log in after successful registration
      const userData = await loginUser({
        username: registerForm.username,
        password: registerForm.password
      });
      
      setUser(userData);
      setIsAuthenticated(true);
      setCurrentView('dashboard');
      
      // Reset form
      setRegisterForm({ username: '', email: '', password: '', confirmPassword: '' });
    } catch (err) {
      setError(err.message || 'Failed to register. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      setIsLoading(true);
      await logoutUser();
      setUser(null);
      setIsAuthenticated(false);
      setCurrentView('login');
      setDashboardData(null);
    } catch (err) {
      console.error('Logout error:', err);
      // Still logout the user on the frontend even if API fails
      setUser(null);
      setIsAuthenticated(false);
      setCurrentView('login');
    } finally {
      setIsLoading(false);
    }
  };

  // 6. API Calls
  const API_BASE = '/api';

  const checkAuthStatus = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_BASE}/user`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
        setIsAuthenticated(true);
        setCurrentView('dashboard');
      }
    } catch (err) {
      console.error('Auth check error:', err);
      // Not authenticated - stay on login page
    } finally {
      setIsLoading(false);
    }
  };

  const loginUser = async (credentials) => {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(credentials)
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    return data.user;
  };

  const registerUser = async (userData) => {
    const { confirmPassword, ...registerData } = userData;
    
    const response = await fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(registerData)
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      if (data.details) {
        // Handle validation errors from backend
        const backendErrors = {};
        Object.entries(data.details).forEach(([key, value]) => {
          backendErrors[key] = value;
        });
        setRegisterErrors(backendErrors);
        throw new Error('Validation failed');
      }
      throw new Error(data.error || 'Registration failed');
    }
    
    return data;
  };

  const logoutUser = async () => {
    const response = await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || 'Logout failed');
    }
    
    return true;
  };

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE}/dashboard`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Session expired or unauthorized
          setUser(null);
          setIsAuthenticated(false);
          setCurrentView('login');
          throw new Error('Authentication required. Please login again.');
        }
        throw new Error('Failed to fetch dashboard data');
      }
      
      const data = await response.json();
      setDashboardData(data.dashboardData);
    } catch (err) {
      console.error('Dashboard data error:', err);
      setError(err.message);
    }
  };

  // 7. Render Methods
  const renderLogin = () => {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>Login</h2>
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="username">Username or Email</label>
              <input
                type="text"
                id="username"
                name="username"
                value={loginForm.username}
                onChange={handleLoginInputChange}
                placeholder="Enter your username or email"
                disabled={isLoading}
              />
              {loginErrors.username && <span className="field-error">{loginErrors.username}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={loginForm.password}
                onChange={handleLoginInputChange}
                placeholder="Enter your password"
                disabled={isLoading}
              />
              {loginErrors.password && <span className="field-error">{loginErrors.password}</span>}
            </div>
            
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Logging in...' : 'Login'}
            </button>
          </form>
          
          <div className="auth-footer">
            <p>Don't have an account?</p>
            <button 
              onClick={() => handleViewChange('register')} 
              className="btn btn-link"
              disabled={isLoading}
            >
              Register
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderRegister = () => {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>Create Account</h2>
          {error && <div className="error-message">{error}</div>}
          
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label htmlFor="reg-username">Username</label>
              <input
                type="text"
                id="reg-username"
                name="username"
                value={registerForm.username}
                onChange={handleRegisterInputChange}
                placeholder="Choose a username"
                disabled={isLoading}
              />
              {registerErrors.username && <span className="field-error">{registerErrors.username}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="reg-email">Email</label>
              <input
                type="email"
                id="reg-email"
                name="email"
                value={registerForm.email}
                onChange={handleRegisterInputChange}
                placeholder="Enter your email"
                disabled={isLoading}
              />
              {registerErrors.email && <span className="field-error">{registerErrors.email}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="reg-password">Password</label>
              <input
                type="password"
                id="reg-password"
                name="password"
                value={registerForm.password}
                onChange={handleRegisterInputChange}
                placeholder="Create a password"
                disabled={isLoading}
              />
              {registerErrors.password && <span className="field-error">{registerErrors.password}</span>}
            </div>
            
            <div className="form-group">
              <label htmlFor="reg-confirm-password">Confirm Password</label>
              <input
                type="password"
                id="reg-confirm-password"
                name="confirmPassword"
                value={registerForm.confirmPassword}
                onChange={handleRegisterInputChange}
                placeholder="Confirm your password"
                disabled={isLoading}
              />
              {registerErrors.confirmPassword && <span className="field-error">{registerErrors.confirmPassword}</span>}
            </div>
            
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? 'Registering...' : 'Register'}
            </button>
          </form>
          
          <div className="auth-footer">
            <p>Already have an account?</p>
            <button 
              onClick={() => handleViewChange('login')} 
              className="btn btn-link"
              disabled={isLoading}
            >
              Login
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderDashboard = () => {
    return (
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <button onClick={handleLogout} className="btn btn-logout" disabled={isLoading}>
            {isLoading ? 'Logging out...' : 'Logout'}
          </button>
        </header>
        
        {error && <div className="error-message">{error}</div>}
        
        <div className="dashboard-content">
          {!dashboardData ? (
            <div className="loading-spinner">Loading dashboard data...</div>
          ) : (
            <>
              <div className="welcome-card">
                <h2>{dashboardData.welcomeMessage}</h2>
                <p>Last login: {dashboardData.lastLogin}</p>
              </div>
              
              <div className="stats-container">
                <div className="stat-card">
                  <h3>Visits</h3>
                  <p className="stat-value">{dashboardData.stats.visits}</p>
                </div>
                
                <div className="stat-card">
                  <h3>Activities</h3>
                  <p className="stat-value">{dashboardData.stats.activities}</p>
                </div>
              </div>
              
              <div className="dashboard-section">
                <h3>Recent Activity</h3>
                <p>This is a protected section of the dashboard. Only authenticated users can see this content.</p>
                <div className="dashboard-action-buttons">
                  <button className="btn btn-secondary">View Profile</button>
                  <button className="btn btn-secondary">Account Settings</button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    );
  };
  
  // Main render method
  return (
    <main className="app">
      {isLoading && currentView === 'initial' && (
        <div className="initial-loading">
          <div className="loading-spinner"></div>
          <p>Loading application...</p>
        </div>
      )}
      
      {currentView === 'login' && renderLogin()}
      {currentView === 'register' && renderRegister()}
      {currentView === 'dashboard' && renderDashboard()}
    </main>
  );
}

// 8. Mounting Logic
const root = createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
