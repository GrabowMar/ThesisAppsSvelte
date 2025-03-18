import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      fetchBalance();
      fetchTransactions();
    }
  }, [user]);

  const fetchBalance = async () => {
    const response = await axios.get(`http://localhost:5117/balance/${user.user_id}`);
    setBalance(response.data.balance);
  };

  const fetchTransactions = async () => {
    const response = await axios.get(`http://localhost:5117/transactions/${user.user_id}`);
    setTransactions(response.data);
  };

  const handleLogin = async (username, password) => {
    const response = await axios.post('http://localhost:5117/login', { username, password });
    setUser(response.data);
    navigate('/dashboard');
  };

  const handleRegister = async (username, password) => {
    const response = await axios.post('http://localhost:5117/register', { username, password });
    setUser(response.data);
    navigate('/dashboard');
  };

  const handleSend = async (receiverAddress, amount) => {
    await axios.post('http://localhost:5117/send', {
      sender_id: user.user_id,
      receiver_address: receiverAddress,
      amount: parseFloat(amount)
    });
    fetchBalance();
    fetchTransactions();
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LoginPage onLogin={handleLogin} onRegister={handleRegister} />} />
        <Route path="/dashboard" element={<Dashboard user={user} balance={balance} transactions={transactions} onSend={handleSend} />} />
      </Routes>
    </Router>
  );
};

const LoginPage = ({ onLogin, onRegister }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  return (
    <div className="login-page">
      <h2>Login</h2>
      <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button onClick={() => onLogin(username, password)}>Login</button>
      <button onClick={() => onRegister(username, password)}>Register</button>
    </div>
  );
};

const Dashboard = ({ user, balance, transactions, onSend }) => {
  const [receiverAddress, setReceiverAddress] = useState('');
  const [amount, setAmount] = useState('');

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <p>Your Address: {user.address}</p>
      <p>Balance: {balance}</p>
      <h3>Send Crypto</h3>
      <input type="text" placeholder="Receiver Address" value={receiverAddress} onChange={(e) => setReceiverAddress(e.target.value)} />
      <input type="number" placeholder="Amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
      <button onClick={() => onSend(receiverAddress, amount)}>Send</button>
      <h3>Transaction History</h3>
      <ul>
        {transactions.map((tx, index) => (
          <li key={index}>
            {tx.sender_id === user.user_id ? 'Sent' : 'Received'} {tx.amount} to {tx.sender_id === user.user_id ? tx.receiver_id : tx.sender_id}
          </li>
        ))}
      </ul>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
