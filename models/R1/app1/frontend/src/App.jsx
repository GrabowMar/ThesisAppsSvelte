import { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [dashboardData, setDashboardData] = useState('');

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/dashboard', { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data.message);
        setCurrentPage('dashboard');
      }
    } catch (err) {
      console.error('Auth check failed:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const endpoint = currentPage === 'login' ? '/api/login' : '/api/register';
    
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include'
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error);

      if (currentPage === 'login') {
        await checkAuthStatus();
      } else {
        setCurrentPage('login');
        setUsername('');
        setPassword('');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = async () => {
    await fetch('/api/logout', {
      method: 'POST',
      credentials: 'include'
    });
    setCurrentPage('login');
  };

  const renderForm = () => (
    <form onSubmit={handleSubmit} className="auth-form">
      <h2>{currentPage.toUpperCase()}</h2>
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
      <button type="submit">Submit</button>
      {error && <p className="error">{error}</p>}
      <p>
        {currentPage === 'login' 
          ? "Don't have an account? " 
          : "Already have an account? "}
        <button 
          type="button" 
          onClick={() => setCurrentPage(currentPage === 'login' ? 'register' : 'login')}
        >
          {currentPage === 'login' ? 'Register' : 'Login'}
        </button>
      </p>
    </form>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <h1>{dashboardData}</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );

  return (
    <main>
      {currentPage === 'dashboard' ? renderDashboard() : renderForm()}
    </main>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
