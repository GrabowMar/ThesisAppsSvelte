import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const API_URL = 'http://localhost:5241/api';

function App() {
  const [page, setPage] = useState('login'); // Define login/register/dashboard pages
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [message, setMessage] = useState('');
  const [authenticatedUser, setAuthenticatedUser] = useState(null);

  const handleFormChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleRegister = async () => {
    const res = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    setMessage(data.message || data.error);
  };

  const handleLogin = async () => {
    const res = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    const data = await res.json();
    if (res.ok) {
      setAuthenticatedUser(data.username);
      setPage('dashboard');
    }
    setMessage(data.message || data.error);
  };

  const handleLogout = async () => {
    await fetch(`${API_URL}/logout`, { method: 'POST' });
    setAuthenticatedUser(null);
    setPage('login');
  };

  const handleNavigate = (targetPage) => setPage(targetPage);

  return (
    <div className="App">
      <h1>Flask + React Auth System</h1>
      {message && <p className="message">{message}</p>}

      {page === 'login' && (
        <div className="login">
          <h2>Login</h2>
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleFormChange}
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleFormChange}
          />
          <button onClick={handleLogin}>Login</button>
          <p>
            Don't have an account?{' '}
            <button onClick={() => handleNavigate('register')}>Register</button>
          </p>
        </div>
      )}

      {page === 'register' && (
        <div className="register">
          <h2>Register</h2>
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={formData.username}
            onChange={handleFormChange}
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={formData.password}
            onChange={handleFormChange}
          />
          <button onClick={handleRegister}>Register</button>
          <p>
            Already have an account?{' '}
            <button onClick={() => handleNavigate('login')}>Login</button>
          </p>
        </div>
      )}

      {page === 'dashboard' && (
        <div className="dashboard">
          <h2>Welcome {authenticatedUser}</h2>
          <p>You are now logged in.</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
