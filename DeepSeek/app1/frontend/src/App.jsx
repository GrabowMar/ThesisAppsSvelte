import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';

const App = () => {
  const [page, setPage] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loggedInUser, setLoggedInUser] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('http://localhost:5161/login', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();
      if (response.ok) {
        setLoggedInUser(username);
        setPage('dashboard');
      } else {
        setError(data.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('http://localhost:5161/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();
      if (response.ok) {
        setPage('login');
      } else {
        setError(data.error || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('http://localhost:5161/logout', {
        method: 'POST',
        credentials: 'include'
      });
      setLoggedInUser('');
      setPage('login');
    } catch (err) {
      setError('Logout failed. Please try again.');
    }
  };

  return (
    <div className="app">
      {page === 'login' && (
        <form onSubmit={handleLogin}>
          <h1>Login</h1>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Login</button>
          {error && <p className="error">{error}</p>}
          <p>
            Don't have an account?{' '}
            <button type="button" onClick={() => setPage('register')}>
              Register
            </button>
          </p>
        </form>
      )}

      {page === 'register' && (
        <form onSubmit={handleRegister}>
          <h1>Register</h1>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Register</button>
          {error && <p className="error">{error}</p>}
          <p>
            Already have an account?{' '}
            <button type="button" onClick={() => setPage('login')}>
              Login
            </button>
          </p>
        </form>
      )}

      {page === 'dashboard' && (
        <div>
          <h1>Dashboard</h1>
          <p>Welcome, {loggedInUser}!</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
