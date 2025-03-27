import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import './App.css';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleRegister = async () => {
    const response = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    setMessage(data.message);
  };

  const handleLogin = async () => {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (response.status === 200) {
      setIsAuthenticated(true);
    }
    setMessage(data.message);
  };

  const handleLogout = async () => {
    await fetch('/api/logout', { method: 'POST' });
    setIsAuthenticated(false);
    setMessage('Logged out successfully');
  };

  return (
    <Router>
      <div>
        <Switch>
          <Route path="/register">
            <h2>Register</h2>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleRegister}>Register</button>
            <p>{message}</p>
          </Route>
          <Route path="/login">
            <h2>Login</h2>
            <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button onClick={handleLogin}>Login</button>
            <p>{message}</p>
          </Route>
          <Route path="/dashboard">
            {isAuthenticated ? (
              <div>
                <h2>Dashboard</h2>
                <p>Welcome to your dashboard</p>
                <button onClick={handleLogout}>Logout</button>
              </div>
            ) : (
              <Redirect to="/login" />
            )}
          </Route>
          <Route path="/">
            <Redirect to="/login" />
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
