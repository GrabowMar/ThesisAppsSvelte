import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [page, setPage] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    checkLoginStatus();
  }, []);

  const checkLoginStatus = async () => {
    try {
      const response = await fetch('/api/user', { credentials: 'include' });
      if (response.ok) {
        setIsLoggedIn(true);
      }
    } catch (err) {
      console.error('Error checking login status:', err);
    }
  };

  const handleRegister = async () => {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setPage('login');
        setError('');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Network error');
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
        setIsLoggedIn(true);
        setError('');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Network error');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', { method: 'POST', credentials: 'include' });
      setIsLoggedIn(false);
    } catch (err) {
      console.error('Error logging out:', err);
    }
  };

  const renderPage = () => {
    if (isLoggedIn) {
      return (
        <div>
          <h1>Welcome, {username}!</h1>
          <button onClick={handleLogout}>Logout</button>
        </div>
      );
    }

    if (page === 'register') {
      return (
        <div>
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
          <button onClick={handleRegister}>Register</button>
          <p>
            Already have an account?{' '}
            <button onClick={() => setPage('login')}>Login</button>
          </p>
          {error && <p className="error">{error}</p>}
        </div>
      );
    }

    return (
      <div>
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
        <p>
          Don't have an account?{' '}
          <button onClick={() => setPage('register')}>Register</button>
        </p>
        {error && <p className="error">{error}</p>}
      </div>
    );
  };

  return <main>{renderPage()}</main>;
};

// Mount the App component to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
