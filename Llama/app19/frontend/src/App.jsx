import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [balance, setBalance] = useState(0.0);
    const [address, setAddress] = useState('');
    const [sender, setSender] = useState('');
    const [recipient, setRecipient] = useState('');
    const [amount, setAmount] = useState(0.0);

    useEffect(() => {
        axios.post('http://localhost:5037/login', {
            username: username,
            password: password
        })
        .then(response => {
            setBalance(response.data.balance);
            setAddress(response.data.address);
        })
        .catch(error => {
            console.error(error);
        });
    }, [username, password]);

    const handleLogin = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5037/login', {
            username: username,
            password: password
        })
        .then(response => {
            setBalance(response.data.balance);
            setAddress(response.data.address);
        })
        .catch(error => {
            console.error(error);
        });
    };

    const handleRegister = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5037/register', {
            username: username,
            password: password
        })
        .then(response => {
            console.log(response);
        })
        .catch(error => {
            console.error(error);
        });
    };

    const handleSend = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5037/send', {
            sender: sender,
            recipient: recipient,
            amount: amount
        })
        .then(response => {
            console.log(response);
        })
        .catch(error => {
            console.error(error);
        });
    };

    const handleReceive = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5037/receive', {
            recipient: recipient,
            amount: amount
        })
        .then(response => {
            console.log(response);
        })
        .catch(error => {
            console.error(error);
        });
    };

    return (
        <div>
            <h1>Crypto Wallet</h1>
            <form onSubmit={handleLogin}>
                <label>Username:</label>
                <input type="text" value={username} onChange={(event) => setUsername(event.target.value)} />
                <br />
                <label>Password:</label>
                <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                <br />
                <input type="submit" value="Login" />
            </form>
            <form onSubmit={handleRegister}>
                <label>Username:</label>
                <input type="text" value={username} onChange={(event) => setUsername(event.target.value)} />
                <br />
                <label>Password:</label>
                <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                <br />
                <input type="submit" value="Register" />
            </form>
            <h2>Balance: {balance}</h2>
            <h2>Address: {address}</h2>
            <form onSubmit={handleSend}>
                <label>Sender:</label>
                <input type="text" value={sender} onChange={(event) => setSender(event.target.value)} />
                <br />
                <label>Recipient:</label>
                <input type="text" value={recipient} onChange={(event) => setRecipient(event.target.value)} />
                <br />
                <label>Amount:</label>
                <input type="number" value={amount} onChange={(event) => setAmount(event.target.value)} />
                <br />
                <input type="submit" value="Send" />
            </form>
            <form onSubmit={handleReceive}>
                <label>Recipient:</label>
                <input type="text" value={recipient} onChange={(event) => setRecipient(event.target.value)} />
                <br />
                <label>Amount:</label>
                <input type="number" value={amount} onChange={(event) => setAmount(event.target.value)} />
                <br />
                <input type="submit" value="Receive" />
            </form>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
