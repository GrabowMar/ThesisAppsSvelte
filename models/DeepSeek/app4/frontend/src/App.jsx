import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [page, setPage] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await fetch('/api/check-session');
      if (response.ok) {
        const data = await response.json();
        setLoggedIn(true);
        setUsername(data.username);
      } else {
        setLoggedIn(false);
      }
    } catch (err) {
      setError('Failed to check session');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        setPage('login');
        setError('');
      } else {
        const data = await response.json();
        setError(data.error);
      }
    } catch (err) {
      setError('Registration failed');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        setLoggedIn(true);
        setError('');
      } else {
        const data = await response.json();
        setError(data.error);
      }
    } catch (err) {
      setError('Login failed');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', { method: 'POST' });
      if (response.ok) {
        setLoggedIn(false);
        setUsername('');
      }
    } catch (err) {
      setError('Logout failed');
    }
  };

  return (
    <main className="container">
      {loggedIn ? (
        <div>
          <h1>Welcome, {username}!</h1>
          <button onClick={handleLogout}>Logout</button>
        </div>
      ) : page === 'login' ? (
        <form onSubmit={handleLogin}>
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
          <button type="submit">Login</button>
          <p>
            Don't have an account?{' '}
            <button onClick={() => setPage('register')}>Register</button>
          </p>
          {error && <p className="error">{error}</p>}
        </form>
      ) : (
        <form onSubmit={handleRegister}>
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
          <button type="submit">Register</button>
          <p>
            Already have an account?{' '}
            <button onClick={() => setPage('login')}>Login</button>
          </p>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </main>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
