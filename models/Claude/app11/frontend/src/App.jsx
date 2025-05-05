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
    return Math.round((votes / poll.totalVotes) * 100);
  };

  if (loading) return <div className="loading">Loading poll details...</div>;
  if (error) return <div className="error-container">{error}</div>;
  if (!poll) return <div className="error-container">Poll not found</div>;

  const isPollExpired = poll.expiresAt && new Date() > new Date(poll.expiresAt);

  return (
    <div className="poll-detail-container">
      <h1>{poll.title}</h1>
      {poll.description && <p className="poll-description">{poll.description}</p>}
      
      <div className="poll-meta">
        <div>Created by: {poll.createdBy.username}</div>
        <div>Total votes: {poll.totalVotes}</div>
        {poll.expiresAt && (
          <div className={`poll-expires ${isPollExpired ? 'expired' : ''}`}>
            {isPollExpired ? 'Expired' : 'Expires'}: {new Date(poll.expiresAt).toLocaleString()}
          </div>
        )}
      </div>

      <div className="poll-options">
        {poll.options.map((option) => (
          <div 
            key={option.id} 
            className={`poll-option ${voteSuccess ? 'results-mode' : ''} ${selectedOption === option.id ? 'selected' : ''}`}
          >
            {!voteSuccess && (
              <div 
                className="option-select" 
                onClick={() => !isPollExpired && !poll.hasVoted && setSelectedOption(option.id)}
              >
                <input 
                  type="radio" 
                  id={option.id} 
                  name="poll-option" 
                  checked={selectedOption === option.id} 
                  onChange={() => setSelectedOption(option.id)}
                  disabled={isPollExpired || poll.hasVoted}
                />
                <label htmlFor={option.id}>{option.text}</label>
              </div>
            )}
            
            {voteSuccess && (
              <div className="option-results">
                <div className="option-text">{option.text}</div>
                <div className="vote-bar-container">
                  <div 
                    className="vote-bar" 
                    style={{ width: `${calculatePercentage(option.votes)}%` }}
                  ></div>
                </div>
                <div className="vote-stats">
                  <span className="vote-percentage">{calculatePercentage(option.votes)}%</span>
                  <span className="vote-count">({option.votes} votes)</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {voteError && <div className="error-message">{voteError}</div>}
      
      {!voteSuccess && !isPollExpired ? (
        <button 
          className="btn-vote" 
          onClick={handleVote} 
          disabled={!selectedOption || poll.hasVoted}
        >
          Submit Vote
        </button>
      ) : (
        <div className="vote-success-message">
          {isPollExpired ? 'This poll has expired.' : 'Thanks for voting!'}
        </div>
      )}
    </div>
  );
}

function CreatePollPage() {
  const { isAuthenticated } = React.useContext(AuthContext);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [options, setOptions] = useState(['', '']);
  const [expiresIn, setExpiresIn] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleAddOption = () => {
    setOptions([...options, '']);
  };

  const handleRemoveOption = (index) => {
    if (options.length <= 2) return;
    const newOptions = [...options];
    newOptions.splice(index, 1);
    setOptions(newOptions);
  };

  const handleOptionChange = (index, value) => {
    const newOptions = [...options];
    newOptions[index] = value;
    setOptions(newOptions);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!title) {
      setError('Please provide a poll title');
      return;
    }

    const filteredOptions = options.filter(option => option.trim() !== '');
    if (filteredOptions.length < 2) {
      setError('Please provide at least two options');
      return;
    }

    try {
      const result = await apiService.createPoll({
        title,
        description,
        options: filteredOptions,
        expiresIn: expiresIn || null
      });

      if (result.success) {
        setSuccess(true);
        setTimeout(() => {
          navigate(`/poll/${result.poll_id}`);
        }, 2000);
      } else {
        setError(result.error || 'Failed to create poll');
      }
    } catch (error) {
      console.error('Error creating poll:', error);
      setError('An unexpected error occurred');
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (success) {
    return (
      <div className="success-container">
        <h2>Poll Created Successfully!</h2>
        <p>Redirecting to your new poll...</p>
      </div>
    );
  }

  return (
    <div className="create-poll-container">
      <h1>Create a New Poll</h1>
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleSubmit} className="poll-form">
        <div className="form-group">
          <label>Poll Title*</label>
          <input 
            type="text" 
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            placeholder="Ask a question..."
          />
        </div>
        
        <div className="form-group">
          <label>Description (Optional)</label>
          <textarea 
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add some details about your poll..."
          ></textarea>
        </div>
        
        <div className="form-group">
          <label>Options*</label>
          <div className="poll-options-list">
            {options.map((option, index) => (
              <div key={index} className="poll-option-input">
                <input 
                  type="text"
                  value={option}
                  onChange={(e) => handleOptionChange(index, e.target.value)}
                  placeholder={`Option ${index + 1}`}
                  required
                />
                {options.length > 2 && (
                  <button 
                    type="button" 
                    className="btn-remove-option"
                    onClick={() => handleRemoveOption(index)}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
            <button 
              type="button" 
              className="btn-add-option"
              onClick={handleAddOption}
            >
              + Add Option
            </button>
          </div>
        </div>
        
        <div className="form-group">
          <label>Poll Duration (Optional)</label>
          <select 
            value={expiresIn} 
            onChange={(e) => setExpiresIn(e.target.value)}
          >
            <option value="">No Expiration</option>
            <option value="1">1 hour</option>
            <option value="6">6 hours</option>
            <option value="12">12 hours</option>
            <option value="24">1 day</option>
            <option value="72">3 days</option>
            <option value="168">1 week</option>
          </select>
        </div>
        
        <button type="submit" className="btn-create-poll">Create Poll</button>
      </form>
    </div>
  );
}

function MyPollsPage() {
  const { isAuthenticated } = React.useContext(AuthContext);
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMyPolls = async () => {
      try {
        setLoading(true);
        const data = await apiService.getMyPolls();
        setPolls(data.polls || []);
      } catch (error) {
        console.error('Error fetching my polls:', error);
        setError('Failed to load your polls');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchMyPolls();
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (loading) return <div className="loading">Loading your polls...</div>;
  if (error) return <div className="error-container">{error}</div>;

  return (
    <div className="my-polls-container">
      <h1>My Polls</h1>
      
      {polls.length === 0 ? (
        <div className="no-polls">
          <p>You haven't created any polls yet.</p>
          <Link to="/create-poll" className="btn-primary">Create Your First Poll</Link>
        </div>
      ) : (
        <div className="polls-list">
          {polls.map((poll) => (
            <div 
              key={poll.id} 
              className={`my-poll-item ${poll.isExpired ? 'expired' : ''}`}
            >
              <div className="poll-header">
                <h3>{poll.title}</h3>
                {poll.isExpired && <span className="expired-badge">Expired</span>}
              </div>
              
              <div className="poll-stats">
                <div className="stat-item">
                  <span className="stat-label">Total Votes:</span>
                  <span className="stat-value">{poll.totalVotes}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Options:</span>
                  <span className="stat-value">{poll.options.length}</span>
                </div>
                {poll.expiresAt && (
                  <div className="stat-item">
                    <span className="stat-label">Expires:</span>
                    <span className="stat-value">
                      {new Date(poll.expiresAt).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
              
              <div className="poll-options-summary">
                {poll.options.slice(0, 3).map((option) => (
                  <div key={option.id} className="option-summary">
                    <span className="option-text">{option.text}</span>
                    <div className="option-votes">
                      <div 
                        className="vote-bar" 
                        style={{ 
                          width: `${poll.totalVotes ? (option.votes / poll.totalVotes) * 100 : 0}%` 
                        }}
                      ></div>
                      <span className="vote-count">{option.votes} votes</span>
                    </div>
                  </div>
                ))}
                {poll.options.length > 3 && (
                  <div className="more-options">
                    + {poll.options.length - 3} more options
                  </div>
                )}
              </div>
              
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

function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const data = await apiService.getAnalytics();
        setAnalytics(data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
        setError('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) return <div className="loading">Loading analytics...</div>;
  if (error) return <div className="error-container">{error}</div>;
  if (!analytics) return <div className="error-container">No analytics data available</div>;

  return (
    <div className="analytics-container">
      <h1>Polling Analytics</h1>
      
      <div className="analytics-summary">
        <div className="analytics-card">
          <h3>Total Polls</h3>
          <div className="analytics-value">{analytics.totalPolls}</div>
        </div>
        <div className="analytics-card">
          <h3>Total Votes</h3>
          <div className="analytics-value">{analytics.totalVotes}</div>
        </div>
        <div className="analytics-card">
          <h3>Active Polls</h3>
          <div className="analytics-value">{analytics.activePolls}</div>
        </div>
      </div>
      
      <div className="analytics-section">
        <h2>Most Popular Polls</h2>
        
        {analytics.popularPolls.length === 0 ? (
          <p>No poll data available yet</p>
        ) : (
          <div className="popular-polls">
            {analytics.popularPolls.map((poll, index) => (
              <div key={poll.id} className="popular-poll-item">
                <div className="poll-rank">{index + 1}</div>
                <div className="poll-title">{poll.title}</div>
                <div className="poll-votes">{poll.voteCount} votes</div>
                <Link to={`/poll/${poll.id}`} className="btn-view">View</Link>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="analytics-section">
        <h2>Recent Activity</h2>
        
        {analytics.recentActivity.length === 0 ? (
          <p>No recent activity</p>
        ) : (
          <div className="recent-activity">
            {analytics.recentActivity.map((activity, index) => (
              <div key={index} className="activity-item">
                <div className="activity-time">
                  {new Date(activity.timestamp).toLocaleString()}
                </div>
                <div className="activity-details">
                  Someone voted for <strong>"{activity.optionText}"</strong> in poll <strong>"{activity.pollTitle}"</strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Protected Route Component
function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = React.useContext(AuthContext);
  
  if (loading) {
    return <div className="loading">Loading...</div>;
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />;
}

// Main App Component
function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <Navbar />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/poll/:id" element={<PollDetailPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route 
                path="/create-poll" 
                element={
                  <PrivateRoute>
                    <CreatePollPage />
                  </PrivateRoute>
                } 
              />
              <Route 
                path="/my-polls" 
                element={
                  <PrivateRoute>
                    <MyPollsPage />
                  </PrivateRoute>
                } 
              />
            </Routes>
          </main>
          <footer className="app-footer">
            <div>PollMaster &copy; {new Date().getFullYear()}</div>
          </footer>
        </div>
      </AuthProvider>
    </Router>
  );
}

// Mount the App to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;


