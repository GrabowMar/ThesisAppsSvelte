import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [user, setUser] = useState(null);
    const [balance, setBalance] = useState(0);
    const [address, setAddress] = useState('');
    const [transactions, setTransactions] = useState([]);

    useEffect(() => {
        fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: 'username',
                password: 'password'
            })
        })
        .then(response => response.json())
        .then(data => {
            setUser(data.user_id);
            setBalance(data.balance);
        });
    }, []);

    const handleSend = (event) => {
        event.preventDefault();
        const senderId = user;
        const receiverId = event.target.receiverId.value;
        const amount = event.target.amount.value;
        fetch('/api/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sender_id: senderId,
                receiver_id: receiverId,
                amount: amount
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert('Transaction successful');
            }
        });
    };

    const handleBalance = () => {
        fetch('/api/balance?user_id=' + user)
        .then(response => response.json())
        .then(data => {
            setBalance(data.balance);
        });
    };

    const handleTransactions = () => {
        fetch('/api/transactions?user_id=' + user)
        .then(response => response.json())
        .then(data => {
            setTransactions(data);
        });
    };

    const handleAddress = () => {
        fetch('/api/address?user_id=' + user)
        .then(response => response.json())
        .then(data => {
            setAddress(data.address);
        });
    };

    return (
        <div>
            <h1>Crypto Wallet</h1>
            <p>Balance: {balance}</p>
            <p>Address: {address}</p>
            <form onSubmit={handleSend}>
                <label>Receiver ID:</label>
                <input type="text" name="receiverId" />
                <label>Amount:</label>
                <input type="number" name="amount" />
                <button type="submit">Send</button>
            </form>
            <button onClick={handleBalance}>Check Balance</button>
            <button onClick={handleTransactions}>View Transactions</button>
            <button onClick={handleAddress}>View Address</button>
            <ul>
                {transactions.map((transaction, index) => (
                    <li key={index}>{transaction.amount} {transaction.sender_id === user ? 'sent to' : 'received from'} {transaction.receiver_id === user ? 'you' : transaction.receiver_id}</li>
                ))}
            </ul>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
