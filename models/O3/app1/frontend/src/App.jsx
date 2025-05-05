// app/frontend/src/App.jsx
import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom';
import './App.css';

// API Base URL (backend runs on port 6141)
const API_BASE = 'http://localhost:6141';

//
// Login Page Component
//
function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  // Handler for input changes
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // Login event handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (!data.success) {
        setError(data.message);
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError('Login request failed.');
    }
  };

  return (
    <div className="container">
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="username"
          placeholder="Username"
          value={formData.username}
          onChange={handleChange}
          required
        />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
        />

        <button type="submit">Login</button>
      </form>

      <p>
        Don't have an account? <Link to="/register">Register here</Link>
      </p>
    </div>
  );
}

//
// Register Page Component
//
function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    try {
      const res = await fetch(`${API_BASE}/register`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await res.json();
      if (!data.success) {
        setError(data.message);
      } else {
        setSuccessMsg('Registration successful, please log in.');
        setTimeout(() => navigate('/login'), 1500);
      }
    } catch (err) {
      setError('Registration request failed.');
    }
  };

  return (
    <div className="container">
      <h2>Register</h2>
      {error && <div className="error">{error}</div>}
      {successMsg && <div className="success">{successMsg}</div>}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="username"
          placeholder="Username"
          value={formData.username}
          onChange={handleChange}
          required
        />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          required
        />

        <button type="submit">Register</button>
      </form>

      <p>
        Already have an account? <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

//
// Dashboard Page Component
//
function Dashboard() {
  const navigate = useNavigate();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // Fetch dashboard data once component is mounted
  React.useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/dashboard`, {
          method: 'GET',
          credentials: 'include',
        });
        const data = await res.json();
        if (!data.success) {
          setError(data.message);
        } else {
          setMessage(data.message);
        }
      } catch (err) {
        setError('Failed to fetch dashboard data.');
      }
    })();
  }, []);

  const handleLogout = async () => {
    try {
      const res = await fetch(`${API_BASE}/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
      if (data.success) {
        navigate('/login');
      }
    } catch (err) {
      // In production, log error
      console.error('Logout error:', err);
    }
  };

  // If not authenticated, you might want to redirect to login.
  if (error) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="container">
      <h2>Dashboard</h2>
      <p>{message}</p>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}

//
// App Component - includes multipage routing
//
function App() {
  return (
    <div>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        {/* Default route */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        {/* Catch-all route */}
        <Route path="*" element={<div className="container"><h2>404: Page Not Found</h2><Link to="/login">Go to Login</Link></div>} />
      </Routes>
    </div>
  );
}

// Mounting logic: attach the App to the DOM element with id "root"
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Router>
    <App />
  </Router>
);

export default App;
