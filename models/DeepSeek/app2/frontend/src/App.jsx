import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [page, setPage] = useState('login');  // 'login' or 'register' or 'dashboard'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth', { credentials: 'include' });
      const data = await response.json();
      if (data.authenticated) {
        setIsAuthenticated(true);
        setPage('dashboard');
      }
    } catch (err) {
      setError('Failed to check authentication status.');
    }
  };

  const handleRegister = async () => {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      const data = await response.json();
      if (response.ok) {
        setPage('login');
        setError('');
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Registration failed. Please try again.');
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      const data = await response.json();
      if (response.ok) {
        setIsAuthenticated(true);
        setPage('dashboard');
        setError('');
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include',
      });
      if (response.ok) {
        setIsAuthenticated(false);
        setPage('login');
        setError('');
      }
    } catch (err) {
      setError('Logout failed. Please try again.');
    }
  };

  return (
    <main>
      {page === 'login' && (
        <div className="auth-form">
          <h1>Login</h1>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={handleLogin}>Login</button>
          {error && <p className="error">{error}</p>}
          <p>
            Don't have an account?{' '}
            <button onClick={() => setPage('register')}>Register</button>
          </p>
        </div>
      )}

      {page === 'register' && (
        <div className="auth-form">
          <h1>Register</h1>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button onClick={handleRegistration}>Register</button>
          {error && <p className="error">{error}</p>}
          <p>
            Already have an account?{' '}
            <button onClick={() => setPage('login')}>Login</button>
          </p>
        </div>
      )}

      {page === 'dashboard' && (
        <div className="dashboard">
          <h1>Welcome, {username}!</h1>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </main>
  );
}

// Mount the app
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
