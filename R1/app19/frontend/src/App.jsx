import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, Link } from 'react-router-dom';
import ReactDOM from 'react-dom/client';

const App = () => {
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    if (token && username) {
      fetchUserData(username, token);
    }
  }, []);

  const fetchUserData = async (username, token) => {
    try {
      const response = await fetch(`http://localhost:5597/api/user/${username}`, {
        headers: { 'Authorization': token }
      });
      
      if (!response.ok) throw new Error('Session expired');
      
      const data = await response.json();
      setUser(username);
      setBalance(data.balance);
      setTransactions(data.transactions);
      setAddresses(data.addresses);
      
    } catch (error) {
      logout();
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setUser(null);
    navigate('/login');
  };

  if (!user) {
    return (
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div className="app">
      <nav>
        <h1>Crypto Wallet</h1>
        <button onClick={logout}>Logout</button>
      </nav>

      <Routes>
        <Route path="/" element={
          <Dashboard balance={balance} transactions={transactions} />
        } />
        <Route path="/send" element={<Send balance={balance} />} />
        <Route path="/addresses" element={<Addresses addresses={addresses} />} />
      </Routes>
    </div>
  );
};

// Auth Components
const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5597/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) throw new Error('Login failed');
      
      const { token, username } = await response.json();
      localStorage.setItem('token', token);
      localStorage.setItem('username', username);
      navigate('/');
      
    } catch (error) {
      alert(error.message);
    }
  };

  return (
    <div className="auth-form">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <input type="text" placeholder="Username" required 
          onChange={(e) => setCredentials({...credentials, username: e.target.value})} />
        <input type="password" placeholder="Password" required 
          onChange={(e) => setCredentials({...credentials, password: e.target.value})} />
        <button type="submit">Login</button>
      </form>
      <Link to="/register">Create account</Link>
    </div>
  );
};

// Wallet Components
const Dashboard = ({ balance, transactions }) => (
  <div className="dashboard">
    <div className="balance-card">
      <h3>Current Balance</h3>
      <p>{balance} BTC</p>
    </div>
    
    <div className="actions">
      <Link to="/send" className="btn">Send Funds</Link>
      <Link to="/addresses" className="btn">My Addresses</Link>
    </div>

    <div className="transactions">
      <h3>Transaction History</h3>
      <ul>
        {transactions.map((t, i) => (
          <li key={i}>
            {t.sender} → {t.receiver}: {t.amount} BTC
          </li>
        ))}
      </ul>
    </div>
  </div>
);

// Initialize App
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <Router>
    <App />
  </Router>
);
