import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleRegister = async () => {
    const response = await fetch('http://localhost:5501/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    setMessage(data.message);
  };

  const handleLogin = async () => {
    const response = await fetch('http://localhost:5501/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    setMessage(data.message);
  };

  const handleLogout = async () => {
    const response = await fetch('http://localhost:5501/logout', {
      method: 'POST',
    });
    const data = await response.json();
    setMessage(data.message);
  };

  return (
    <Router>
      <div>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/register">Register</Link>
          <Link to="/login">Login</Link>
          <Link to="/dashboard">Dashboard</Link>
          <button onClick={handleLogout}>Logout</button>
        </nav>
        <Routes>
          <Route path="/register" element={
            <div>
              <h2>Register</h2>
              <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button onClick={handleRegister}>Register</button>
              <p>{message}</p>
            </div>
          } />
          <Route path="/login" element={
            <div>
              <h2>Login</h2>
              <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
              <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
              <button onClick={handleLogin}>Login</button>
              <p>{message}</p>
            </div>
          } />
          <Route path="/dashboard" element={
            <div>
              <h2>Dashboard</h2>
              <p>{message}</p>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
