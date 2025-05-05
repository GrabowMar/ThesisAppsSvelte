import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [page, setPage] = useState('login');
  const [error, setError] = useState('');

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('/api/check-auth');
      const data = await response.json();
      if (data.authenticated) {
        setIsAuthenticated(true);
        setUsername(data.username);
      }
    } catch (err) {
      setError('Failed to check authentication status');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const username = formData.get('username');
    const password = formData.get('password');

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        setPage('login'); // Redirect to login page
      } else {
        const data = await response.json();
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to register');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const username = formData.get('username');
    const password = formData.get('password');

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        setIsAuthenticated(true);
        setUsername(username);
      } else {
        const data = await response.json();
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to login');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', { method: 'POST' });
      setIsAuthenticated(false);
      setUsername('');
    } catch (err) {
      setError('Failed to logout');
    }
  };

  if (isAuthenticated) {
    return (
      <div className="dashboard">
        <h1>Welcome, {username}!</h1>
        <button onClick={handleLogout}>Logout</button>
      </div>
    );
  }

  return (
    <div className="auth">
      {page === 'login' ? (
        <form onSubmit={handleLogin}>
          <h1>Login</h1>
          <input type="text" name="username" placeholder="Username" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Login</button>
          <p>
            Don't have an account?{' '}
            <button type="button" onClick={() => setPage('register')}>
              Register
            </button>
          </p>
          {error && <p className="error">{error}</p>}
        </form>
      ) : (
        <form onSubmit={handleRegister}>
          <h1>Register</h1>
          <input type="text" name="username" placeholder="Username" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit">Register</button>
          <p>
            Already have an account?{' '}
            <button type="button" onClick={() => setPage('login')}>
              Login
            </button>
          </p>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  );
};

// Mount the app
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
