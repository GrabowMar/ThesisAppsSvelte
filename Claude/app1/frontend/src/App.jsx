import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API service to handle backend requests
const API_BASE_URL = 'http://localhost:5321/api';

const apiService = {
  register: async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
        credentials: 'include',
      });
      return await response.json();
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, message: 'Network error occurred' };
    }
  },

  login: async (credentials) => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
        credentials: 'include',
      });
      return await response.json();
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, message: 'Network error occurred' };
    }
  },

  logout: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      return await response.json();
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, message: 'Network error occurred' };
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/user`, {
        method: 'GET',
        credentials: 'include',
      });
      return await response.json();
    } catch (error) {
      console.error('Get user error:', error);
      return { success: false, message: 'Network error occurred' };
    }
  },
};

// Main App Component
function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is logged in on component mount
  useEffect(() => {
    const checkAuthStatus = async () => {
      setIsLoading(true);
      const response = await apiService.getCurrentUser();
      if (response.success) {
        setIsLoggedIn(true);
        setUser(response.user);
        setCurrentPage('dashboard');
      }
      setIsLoading(false);
    };

    checkAuthStatus();
  }, []);

  // Handle navigation
  const navigateTo = (page) => {
    setCurrentPage(page);
  };

  // Handle logout
  const handleLogout = async () => {
    setIsLoading(true);
    const response = await apiService.logout();
    if (response.success) {
      setIsLoggedIn(false);
      setUser(null);
      setCurrentPage('login');
    } else {
      alert(response.message || 'Failed to logout');
    }
    setIsLoading(false);
  };

  // Render pages based on current state
  const renderPage = () => {
    if (isLoading) {
      return <LoadingSpinner />;
    }

    switch (currentPage) {
      case 'login':
        return <LoginPage navigateTo={navigateTo} setIsLoggedIn={setIsLoggedIn} setUser={setUser} />;
      case 'register':
        return <RegisterPage navigateTo={navigateTo} />;
      case 'dashboard':
        return <Dashboard user={user} handleLogout={handleLogout} />;
      case 'profile':
        return <ProfilePage user={user} handleLogout={handleLogout} navigateTo={navigateTo} />;
      default:
        return <LoginPage navigateTo={navigateTo} setIsLoggedIn={setIsLoggedIn} setUser={setUser} />;
    }
  };

  return (
    <div className="app-container">
      <Header 
        isLoggedIn={isLoggedIn} 
        currentPage={currentPage} 
        navigateTo={navigateTo} 
        handleLogout={handleLogout} 
      />
      <main className="main-content">
        {renderPage()}
      </main>
      <Footer />
    </div>
  );
}

// Header Component
function Header({ isLoggedIn, currentPage, navigateTo, handleLogout }) {
  return (
    <header className="app-header">
      <div className="logo" onClick={() => navigateTo(isLoggedIn ? 'dashboard' : 'login')}>
        <h1>Auth<span>System</span></h1>
      </div>
      <nav className="nav-menu">
        {isLoggedIn ? (
          <>
            <button 
              className={`nav-button ${currentPage === 'dashboard' ? 'active' : ''}`} 
              onClick={() => navigateTo('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={`nav-button ${currentPage === 'profile' ? 'active' : ''}`} 
              onClick={() => navigateTo('profile')}
            >
              Profile
            </button>
            <button className="nav-button logout" onClick={handleLogout}>
              Logout
            </button>
          </>
        ) : (
          <>
            <button 
              className={`nav-button ${currentPage === 'login' ? 'active' : ''}`} 
              onClick={() => navigateTo('login')}
            >
              Login
            </button>
            <button 
              className={`nav-button ${currentPage === 'register' ? 'active' : ''}`} 
              onClick={() => navigateTo('register')}
            >
              Register
            </button>
          </>
        )}
      </nav>
    </header>
  );
}

// Login Page Component
function LoginPage({ navigateTo, setIsLoggedIn, setUser }) {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials({ ...credentials, [name]: value });
    // Clear errors when typing
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' });
    }
    if (apiError) {
      setApiError('');
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!credentials.username.trim()) {
      newErrors.username = 'Username or email is required';
    }
    if (!credentials.password) {
      newErrors.password = 'Password is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setApiError('');

    const response = await apiService.login(credentials);
    
    setIsLoading(false);
    
    if (response.success) {
      setUser(response.user);
      setIsLoggedIn(true);
      navigateTo('dashboard');
    } else {
      setApiError(response.message || 'Login failed');
    }
  };

  return (
    <div className="auth-form-container">
      <h2>Login to Your Account</h2>
      <p className="form-subtitle">Enter your credentials to access your dashboard</p>
      
      {apiError && <div className="error-message">{apiError}</div>}
      
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username or Email</label>
          <input
            type="text"
            id="username"
            name="username"
            value={credentials.username}
            onChange={handleChange}
            placeholder="Enter your username or email"
            className={errors.username ? 'input-error' : ''}
          />
          {errors.username && <div className="error-text">{errors.username}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={credentials.password}
            onChange={handleChange}
            placeholder="Enter your password"
            className={errors.password ? 'input-error' : ''}
          />
          {errors.password && <div className="error-text">{errors.password}</div>}
        </div>
        
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      
      <div className="auth-form-footer">
        <p>
          Don't have an account?{' '}
          <span className="text-link" onClick={() => navigateTo('register')}>
            Register here
          </span>
        </p>
      </div>
    </div>
  );
}

// Register Page Component
function RegisterPage({ navigateTo }) {
  const [userData, setUserData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [formSubmitted, setFormSubmitted] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserData({ ...userData, [name]: value });
    // Clear errors when typing
    if (errors[name]) {
      setErrors({ ...errors, [name]: '' });
    }
    if (apiError) {
      setApiError('');
    }
  };

  const validateForm = () => {
    const newErrors = {};
    // Username validation
    if (!userData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (userData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }
    
    // Email validation
    if (!userData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(userData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    // Password validation
    if (!userData.password) {
      newErrors.password = 'Password is required';
    } else if (userData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/[0-9]/.test(userData.password)) {
      newErrors.password = 'Password must contain at least one number';
    } else if (!/[A-Z]/.test(userData.password)) {
      newErrors.password = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(userData.password)) {
      newErrors.password = 'Password must contain at least one lowercase letter';
    }
    
    // Confirm password validation
    if (!userData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (userData.password !== userData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    setApiError('');

    const response = await apiService.register(userData);
    
    setIsLoading(false);
    
    if (response.success) {
      setFormSubmitted(true);
      setTimeout(() => {
        navigateTo('login');
      }, 2000);
    } else {
      setApiError(response.message || 'Registration failed');
    }
  };

  if (formSubmitted) {
    return (
      <div className="auth-form-container success-container">
        <div className="success-icon">✓</div>
        <h2>Registration Successful!</h2>
        <p>Your account has been created. Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="auth-form-container">
      <h2>Create Your Account</h2>
      <p className="form-subtitle">Fill in your details to get started</p>
      
      {apiError && <div className="error-message">{apiError}</div>}
      
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={userData.username}
            onChange={handleChange}
            placeholder="Choose a username"
            className={errors.username ? 'input-error' : ''}
          />
          {errors.username && <div className="error-text">{errors.username}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={userData.email}
            onChange={handleChange}
            placeholder="Enter your email"
            className={errors.email ? 'input-error' : ''}
          />
          {errors.email && <div className="error-text">{errors.email}</div>}
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={userData.password}
            onChange={handleChange}
            placeholder="Create a password"
            className={errors.password ? 'input-error' : ''}
          />
          {errors.password && <div className="error-text">{errors.password}</div>}
          <div className="password-requirements">
            Password must be at least 8 characters with numbers, uppercase and lowercase letters
          </div>
        </div>
        
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={userData.confirmPassword}
            onChange={handleChange}
            placeholder="Confirm your password"
            className={errors.confirmPassword ? 'input-error' : ''}
          />
          {errors.confirmPassword && <div className="error-text">{errors.confirmPassword}</div>}
        </div>
        
        <button type="submit" className="submit-button" disabled={isLoading}>
          {isLoading ? 'Creating Account...' : 'Register'}
        </button>
      </form>
      
      <div className="auth-form-footer">
        <p>
          Already have an account?{' '}
          <span className="text-link" onClick={() => navigateTo('login')}>
            Login here
          </span>
        </p>
      </div>
    </div>
  );
}

// Dashboard Component
function Dashboard({ user, handleLogout }) {
  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <div className="dashboard-container">
      <div className="welcome-section">
        <h2>Welcome, {user.username}!</h2>
        <p>You're now logged into your secure dashboard.</p>
      </div>
      
      <div className="dashboard-content">
        <div className="dashboard-card">
          <h3>Your Account Information</h3>
          <div className="account-info">
            <div className="info-item">
              <span className="info-label">Username:</span>
              <span className="info-value">{user.username}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Email:</span>
              <span className="info-value">{user.email}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Account Created:</span>
              <span className="info-value">
                {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="dashboard-card">
          <h3>Security Recommendations</h3>
          <ul className="security-tips">
            <li>Keep your password secure and never share it</li>
            <li>Update your password regularly</li>
            <li>Enable two-factor authentication for additional security</li>
            <li>Log out when using shared devices</li>
          </ul>
        </div>
      </div>
      
      <div className="action-buttons">
        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

// Profile Page Component
function ProfilePage({ user, handleLogout, navigateTo }) {
  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <div className="profile-avatar">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <h2>{user.username}'s Profile</h2>
      </div>
      
      <div className="profile-details">
        <div className="profile-card">
          <h3>Account Details</h3>
          <div className="detail-item">
            <span className="detail-label">Username:</span>
            <span className="detail-value">{user.username}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Email:</span>
            <span className="detail-value">{user.email}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Member Since:</span>
            <span className="detail-value">
              {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
        </div>
        
        <div className="profile-card">
          <h3>Account Security</h3>
          <p className="security-message">
            For security reasons, password changes must be requested through a secure form.
          </p>
          <button className="profile-action-button" disabled>
            Change Password (Coming Soon)
          </button>
        </div>
      </div>
      
      <div className="profile-actions">
        <button className="back-button" onClick={() => navigateTo('dashboard')}>
          Back to Dashboard
        </button>
        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}

// Loading Spinner Component
function LoadingSpinner() {
  return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <p>Loading...</p>
    </div>
  );
}

// Footer Component
function Footer() {
  return (
    <footer className="app-footer">
      <p>&copy; {new Date().getFullYear()} Auth System. All rights reserved.</p>
    </footer>
  );
}

// Mount the React app to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;