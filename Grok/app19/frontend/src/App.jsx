import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// State Management
const [currentPage, setCurrentPage] = useState('login');
const [token, setToken] = useState(null);
const [balance, setBalance] = useState(0);
const [transactions, setTransactions] = useState([]);
const [addresses, setAddresses] = useState([]);

// API Calls
const apiUrl = 'http://localhost:6017/api';

const fetchBalance = async () => {
  try {
    const response = await fetch(`${apiUrl}/balance`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    setBalance(data.balance);
  } catch (error) {
    console.error('Error fetching balance:', error);
  }
};

const fetchTransactions = async () => {
  try {
    const response = await fetch(`${apiUrl}/transactions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    setTransactions(data);
  } catch (error) {
    console.error('Error fetching transactions:', error);
  }
};

const fetchAddresses = async () => {
  try {
    const response = await fetch(`${apiUrl}/addresses`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    setAddresses(data);
  } catch (error) {
    console.error('Error fetching addresses:', error);
  }
};

const generateNewAddress = async () => {
  try {
    const response = await fetch(`${apiUrl}/addresses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await response.json();
    setAddresses([...addresses, data.address]);
  } catch (error) {
    console.error('Error generating new address:', error);
  }
};

const sendCrypto = async (amount, to) => {
  try {
    const response = await fetch(`${apiUrl}/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ amount, to }),
    });
    const data = await response.json();
    if (response.ok) {
      alert(data.message);
      fetchBalance();
      fetchTransactions();
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error('Error sending crypto:', error);
  }
};

const receiveCrypto = async (amount, from) => {
  try {
    const response = await fetch(`${apiUrl}/receive`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ amount, from }),
    });
    const data = await response.json();
    if (response.ok) {
      alert(data.message);
      fetchBalance();
      fetchTransactions();
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error('Error receiving crypto:', error);
  }
};

// Event Handlers
const handleLogin = async (username, password) => {
  try {
    const response = await fetch('http://localhost:6017/login', {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(`${username}:${password}`),
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();
    if (response.ok) {
      setToken(data.token);
      setCurrentPage('dashboard');
      fetchBalance();
      fetchTransactions();
      fetchAddresses();
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error('Error logging in:', error);
  }
};

const handleRegister = async (username, password) => {
  try {
    const response = await fetch('http://localhost:6017/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    if (response.ok) {
      alert(data.message);
      setCurrentPage('login');
    } else {
      alert(data.message);
    }
  } catch (error) {
    console.error('Error registering:', error);
  }
};

const handleLogout = () => {
  setToken(null);
  setCurrentPage('login');
};

// UI Components
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="login-page">
      <h2>Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={() => handleLogin(username, password)}>Login</button>
      <p>Don't have an account? <span onClick={() => setCurrentPage('register')}>Register</span></p>
    </div>
  );
};

const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="register-page">
      <h2>Register</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button onClick={() => handleRegister(username, password)}>Register</button>
      <p>Already have an account? <span onClick={() => setCurrentPage('login')}>Login</span></p>
    </div>
  );
};

const DashboardPage = () => {
  const [sendAmount, setSendAmount] = useState('');
  const [sendTo, setSendTo] = useState('');
  const [receiveAmount, setReceiveAmount] = useState('');
  const [receiveFrom, setReceiveFrom] = useState('');

  return (
    <div className="dashboard-page">
      <h2>Dashboard</h2>
      <div className="balance">
        <h3>Balance: {balance}</h3>
      </div>
      <div className="send-receive">
        <div className="send">
          <h3>Send Crypto</h3>
          <input
            type="number"
            placeholder="Amount"
            value={sendAmount}
            onChange={(e) => setSendAmount(e.target.value)}
          />
          <input
            type="text"
            placeholder="To"
            value={sendTo}
            onChange={(e) => setSendTo(e.target.value)}
          />
          <button onClick={() => sendCrypto(sendAmount, sendTo)}>Send</button>
        </div>
        <div className="receive">
          <h3>Receive Crypto</h3>
          <input
            type="number"
            placeholder="Amount"
            value={receiveAmount}
            onChange={(e) => setReceiveAmount(e.target.value)}
          />
          <input
            type="text"
            placeholder="From"
            value={receiveFrom}
            onChange={(e) => setReceiveFrom(e.target.value)}
          />
          <button onClick={() => receiveCrypto(receiveAmount, receiveFrom)}>Receive</button>
        </div>
      </div>
      <div className="transactions">
        <h3>Transaction History</h3>
        <ul>
          {transactions.map((transaction, index) => (
            <li key={index}>
              {transaction.type === 'send' ? 'Sent' : 'Received'} {transaction.amount} to/from {transaction.type === 'send' ? transaction.to : transaction.from} on {new Date(transaction.timestamp).toLocaleString()}
            </li>
          ))}
        </ul>
      </div>
      <div className="addresses">
        <h3>Addresses</h3>
        <ul>
          {addresses.map((address, index) => (
            <li key={index}>{address}</li>
          ))}
        </ul>
        <button onClick={generateNewAddress}>Generate New Address</button>
      </div>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
};

// Main App Component
const App = () => {
  useEffect(() => {
    if (token) {
      fetchBalance();
      fetchTransactions();
      fetchAddresses();
    }
  }, [token]);

  return (
    <div className="app">
      {currentPage === 'login' && <LoginPage />}
      {currentPage === 'register' && <RegisterPage />}
      {currentPage === 'dashboard' && token && <DashboardPage />}
    </div>
  );
};

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
