import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Main App Component
function App() {
  const [currentPage, setCurrentPage] = useState('home');
  const [user, setUser] = useState(null);
  const [progress, setProgress] = useState(null);

  // Backend API URLs
  const API_URL = 'http://localhost:5283/api';

  // Event handlers
  const handleLogin = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');

    const res = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (res.ok) {
      setUser(username);
      loadProgress(username);
    } else {
      alert((await res.json()).error || 'Login failed!');
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const username = formData.get('username');
    const password = formData.get('password');
    const language = formData.get('language');

    const res = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, language }),
    });

    if (res.ok) {
      alert('Registration successful! Please login.');
      setCurrentPage('login');
    } else {
      alert((await res.json()).error || 'Registration failed!');
    }
  };

  const loadProgress = async (username) => {
    const res = await fetch(`${API_URL}/progress/${username}`);
    if (res.ok) {
      const data = await res.json();
      setProgress(data);
      setCurrentPage('dashboard');
    } else {
      alert((await res.json()).error || "Couldn't load progress!");
    }
  };

  const logout = () => {
    setUser(null);
    setProgress(null);
    setCurrentPage('home');
  };

  // Pages
  const HomePage = () => (
    <div>
      <h1>Welcome to Language Learning App</h1>
      <button onClick={() => setCurrentPage('login')}>Login</button>
      <button onClick={() => setCurrentPage('register')}>Register</button>
    </div>
  );

  const LoginPage = () => (
    <div>
      <h1>Login</h1>
      <form onSubmit={handleLogin}>
        <input name="username" placeholder="Username" required />
        <input name="password" placeholder="Password" type="password" required />
        <button type="submit">Login</button>
      </form>
    </div>
  );

  const RegisterPage = () => (
    <div>
      <h1>Register</h1>
      <form onSubmit={handleRegister}>
        <input name="username" placeholder="Username" required />
        <input name="password" placeholder="Password" type="password" required />
        <input name="language" placeholder="Preferred Language" required />
        <button type="submit">Register</button>
      </form>
    </div>
  );

  const DashboardPage = () => (
    <div>
      <h1>Dashboard</h1>
      <p>Welcome, {user}!</p>
      <h2>Progress</h2>
      <p>Vocabulary: {progress.vocabulary.length} words</p>
      <p>Quiz Scores: {progress.quiz_scores.join(', ')}</p>
      <button onClick={logout}>Logout</button>
    </div>
  );

  // Render page conditionally
  return (
    <div>
      {currentPage === 'home' && <HomePage />}
      {currentPage === 'login' && <LoginPage />}
      {currentPage === 'register' && <RegisterPage />}
      {currentPage === 'dashboard' && progress && <DashboardPage />}
    </div>
  );
}

// Mount App to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
