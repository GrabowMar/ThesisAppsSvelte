import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link, useNavigate } from 'react-router-dom';
import './App.css';

const App = () => {
    const [user, setUser] = useState(null);
    const [address, setAddress] = useState('');
    const [balance, setBalance] = useState(0);
    const [transactionHistory, setTransactionHistory] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        if (user) {
            fetch(`/api/balance/${user.address}`)
                .then(response => response.json())
                .then(data => setBalance(data.balance));

            fetch(`/api/history/${user.address}`)
                .then(response => response.json())
                .then(data => setTransactionHistory(data.transactions));
        }
    }, [user]);

    const handleLogin = (e) => {
        e.preventDefault();
        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ address })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    setUser(data);
                }
            });
    };

    const handleSend = (e) => {
        e.preventDefault();
        const { to, amount } = Object.fromEntries(new FormData(e.target));
        fetch('/api/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ from: user.address, to, amount: Number(amount) })
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert('Transaction successful');
                    navigate('/dashboard');
                }
            });
    };

    return (
        <Router>
            <nav>
                <Link to="/">Home</Link>
                <Link to="/dashboard">Dashboard</Link>
                <Link to="/login">Login</Link>
            </nav>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={
                    <form onSubmit={handleLogin}>
                        <input type="text" placeholder="Address" value={address} onChange={e => setAddress(e.target.value)} />
                        <button type="submit">Login</button>
                    </form>
                } />
                <Route path="/dashboard" element={
                    user ? (
                        <div>
                            <h2>Dashboard</h2>
                            <p>Balance: {balance}</p>
                            <h3>Transaction History</h3>
                            <ul>
                                {transactionHistory.map((tx, index) => (
                                    <li key={index}>{tx.from} sent {tx.amount} to {tx.to}</li>
                                ))}
                            </ul>
                            <form onSubmit={handleSend}>
                                <input type="text" name="to" placeholder="To Address" required />
                                <input type="number" name="amount" placeholder="Amount" required />
                                <button type="submit">Send</button>
                            </form>
                        </div>
                    ) : (
                        <div>Please login to view the dashboard</div>
                    )
                } />
            </Routes>
        </Router>
    );
};

const Home = () => <h2>Welcome to Crypto Wallet</h2>;

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
