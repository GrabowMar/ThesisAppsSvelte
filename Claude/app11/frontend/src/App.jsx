import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link, Navigate, useParams, useNavigate } from 'react-router-dom';
import './App.css';

// API Service
const API_URL = 'http://localhost:5341/api';

const apiService = {
  // Auth APIs
  register: async (userData) => {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  },

  login: async (credentials) => {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    return response.json();
  },

  logout: async () => {
    const response = await fetch(`${API_URL}/logout`, {
      method: 'POST',
      credentials: 'include'
    });
    return response.json();
  },

  getCurrentUser: async () => {
    const response = await fetch(`${API_URL}/user`, {
      credentials: 'include'
    });
    return response.json();
  },

  // Poll APIs
  getPolls: async () => {
    const response = await fetch(`${API_URL}/polls`, {
      credentials: 'include'
    });
    return response.json();
  },

  getPoll: async (id) => {
    const response = await fetch(`${API_URL}/polls/${id}`, {
      credentials: 'include'
    });
    return response.json();
  },

  createPoll: async (pollData) => {
    const response = await fetch(`${API_URL}/polls`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pollData)
    });
    return response.json();
  },

  vote: async (pollId, optionId) => {
    const response = await fetch(`${API_URL}/polls/${pollId}/vote`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ option_id: optionId })
    });
    return response.json();
  },

  getMyPolls: async () => {
    const response = await fetch(`${API_URL}/my-polls`, {
      credentials: 'include'
    });
    return response.json();
  },

  getAnalytics: async () => {
    const response = await fetch(`${API_URL}/analytics`, {
      credentials: 'include'
    });
    return response.json();
  }
};

// Context for Auth
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const data = await apiService.getCurrentUser();
        if (data.authenticated) {
          setUser(data.user);
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials) => {
    try {
      const data = await apiService.login(credentials);
      if (data.success) {
        setUser(data.user);
        return { success: true };
      }
      return { success: false, error: data.error };
    } catch (error) {
      return { success: false, error: 'Login failed. Please try again.' };
    }
  };

  const register = async (userData) => {
    try {
      const data = await apiService.register(userData);
      return { success: data.success, error: data.error };
    } catch (error) {
      return { success: false, error: 'Registration failed. Please try again.' };
    }
  };

  const logout = async () => {
    try {
      await apiService.logout();
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Components
function Navbar() {
  const { user, logout, isAuthenticated } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-logo">
        <Link to="/">PollMaster</Link>
      </div>
      <div className="navbar-links">
        <Link to="/">Home</Link>
        <Link to="/analytics">Analytics</Link>
        {isAuthenticated ? (
          <>
            <Link to="/create-poll">Create Poll</Link>
            <Link to="/my-polls">My Polls</Link>
            <div className="user-menu">
              <span>{user.username}</span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please fill in all fields');
      return;
    }

    const result = await login({ username, password });
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Login failed. Please try again.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h2>Login</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary">Login</button>
        </form>
        <p>
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}

function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const { register } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username || !email || !password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    const result = await register({ username, email, password });
    if (result.success) {
      navigate('/login');
    } else {
      setError(result.error || 'Registration failed. Please try again.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h2>Register</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary">Register</button>
        </form>
        <p>
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </div>
    </div>
  );
}

function HomePage() {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPolls = async () => {
      try {
        setLoading(true);
        const data = await apiService.getPolls();
        setPolls(data.polls || []);
      } catch (error) {
        console.error('Error fetching polls:', error);
        setError('Failed to load polls. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchPolls();
  }, []);

  if (loading) return <div className="loading">Loading polls...</div>;
  if (error) return <div className="error-container">{error}</div>;

  return (
    <div className="home-container">
      <h1>Active Polls</h1>
      {polls.length === 0 ? (
        <div className="no-polls">
          <p>No active polls available.</p>
        </div>
      ) : (
        <div className="polls-grid">
          {polls.map((poll) => (
            <div className="poll-card" key={poll.id}>
              <h3>{poll.title}</h3>
              {poll.description && <p>{poll.description}</p>}
              <div className="poll-meta">
                <span>Created by: {poll.createdBy.username}</span>
                <span>Total votes: {poll.totalVotes}</span>
              </div>
              {poll.expiresAt && (
                <div className="poll-expires">
                  Expires: {new Date(poll.expiresAt).toLocaleString()}
                </div>
              )}
              <Link to={`/poll/${poll.id}`} className="btn-view-poll">
                View Poll
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PollDetailPage() {
  const { id } = useParams();
  const [poll, setPoll] = useState(null);
  const [selectedOption, setSelectedOption] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [voteSuccess, setVoteSuccess] = useState(false);
  const [voteError, setVoteError] = useState(null);
  
  const fetchPoll = async () => {
    try {
      setLoading(true);
      const data = await apiService.getPoll(id);
      if (data.poll) {
        setPoll(data.poll);
        if (data.poll.hasVoted) {
          setSelectedOption(data.poll.userVote);
          setVoteSuccess(true);
        }
      } else {
        setError('Poll not found');
      }
    } catch (error) {
      console.error('Error fetching poll details:', error);
      setError('Failed to load poll details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPoll();
  }, [id]);

  const handleVote = async () => {
    if (!selectedOption) return;

    try {
      const result = await apiService.vote(id, selectedOption);
      if (result.success) {
        setVoteSuccess(true);
        setVoteError(null);
        // Refresh poll data to get updated votes
        fetchPoll();
      } else {
        setVoteError(result.error || 'Failed to record your vote');
      }
    } catch (error) {
      console.error('Voting error:', error);
      setVoteError('An error occurred while voting');
    }
  };

  const calculatePercentage = (votes) => {
    if (!poll || poll.totalVotes === 0) return 0;
    return Math.round((votes / poll.totalVotes) *
