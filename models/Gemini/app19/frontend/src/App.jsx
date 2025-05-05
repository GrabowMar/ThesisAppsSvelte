import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [address, setAddress] = useState('');
    const [balance, setBalance] = useState(0);
    const [recipient, setRecipient] = useState('');
    const [sendAmount, setSendAmount] = useState('');
    const [receiveAmount, setReceiveAmount] = useState('');
    const [transactions, setTransactions] = useState([]);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [view, setView] = useState('wallet');  // 'wallet', 'send', 'receive', 'transactions'

    useEffect(() => {
        // Check if address exists in local storage
        const storedAddress = localStorage.getItem('walletAddress');
        if (storedAddress) {
            setAddress(storedAddress);
            fetchBalance(storedAddress);
            fetchTransactions(storedAddress);
        }
    }, []);


    const createWallet = async () => {
        try {
            const response = await fetch('/api/create_wallet', { method: 'POST' });
            const data = await response.json();
            if (response.ok) {
                setAddress(data.address);
                setBalance(0);
                setTransactions([]);
                localStorage.setItem('walletAddress', data.address); // Store in local storage
                setMessage(data.message);
                setError('');
            } else {
                setError(data.error || 'Failed to create wallet');
                setMessage('');
            }
        } catch (err) {
            setError('Network error: Could not create wallet');
            setMessage('');
            console.error(err);
        }
    };

    const fetchBalance = async (addr) => {
        try {
            const response = await fetch(`/api/balance/${addr}`);
            const data = await response.json();
            if (response.ok) {
                setBalance(data.balance);
                setError('');
            } else {
                setError(data.error || 'Failed to fetch balance');
            }
        } catch (err) {
            setError('Network error: Could not fetch balance');
            console.error(err);
        }
    };


    const fetchTransactions = async (addr) => {
        try {
            const response = await fetch(`/api/transactions/${addr}`);
            const data = await response.json();
            if (response.ok) {
                setTransactions(data.transactions);
                setError('');
            } else {
                setError(data.error || 'Failed to fetch transactions');
            }
        } catch (err) {
            setError('Network error: Could not fetch transactions');
            console.error(err);
        }
    };



    const sendFunds = async () => {
        try {
            const response = await fetch('/api/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sender: address,
                    recipient: recipient,
                    amount: sendAmount,
                }),
            });
            const data = await response.json();
            if (response.ok) {
                setMessage(data.message);
                setError('');
                fetchBalance(address); // Update balance after sending
                fetchTransactions(address); // Update transaction history
            } else {
                setError(data.error || 'Failed to send funds');
                setMessage('');
            }
        } catch (err) {
            setError('Network error: Could not send funds');
            setMessage('');
            console.error(err);
        }
    };

    const receiveFunds = async () => {
        try {
            const response = await fetch('/api/receive', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    recipient: address,
                    amount: receiveAmount,
                }),
            });
            const data = await response.json();
            if (response.ok) {
                setMessage(data.message);
                setError('');
                fetchBalance(address); // Update balance after receiving
                fetchTransactions(address); // Update transaction history
            } else {
                setError(data.error || 'Failed to receive funds');
                setMessage('');
            }
        } catch (err) {
            setError('Network error: Could not receive funds');
            setMessage('');
            console.error(err);
        }
    };


    return (
        <div className="container">
            <h1>Crypto Wallet</h1>

            {error && <div className="error">{error}</div>}
            {message && <div className="message">{message}</div>}

            {!address ? (
                <button onClick={createWallet}>Create Wallet</button>
            ) : (
                <>
                    <div className="wallet-info">
                        <p><strong>Address:</strong> {address}</p>
                        <p><strong>Balance:</strong> {balance}</p>
                    </div>

                    <div className="navigation">
                        <button onClick={() => setView('wallet')}>Wallet</button>
                        <button onClick={() => setView('send')}>Send</button>
                        <button onClick={() => setView('receive')}>Receive</button>
                        <button onClick={() => setView('transactions')}>Transactions</button>
                    </div>

                    {view === 'wallet' && (
                        <div>
                            <h2>Wallet Overview</h2>
                            <p>View your balance and manage your funds.</p>
                        </div>
                    )}

                    {view === 'send' && (
                        <div className="send-form">
                            <h2>Send Funds</h2>
                            <input
                                type="text"
                                placeholder="Recipient Address"
                                value={recipient}
                                onChange={(e) => setRecipient(e.target.value)}
                            />
                            <input
                                type="number"
                                placeholder="Amount"
                                value={sendAmount}
                                onChange={(e) => setSendAmount(e.target.value)}
                            />
                            <button onClick={sendFunds}>Send</button>
                        </div>
                    )}

                    {view === 'receive' && (
                        <div className="receive-form">
                            <h2>Receive Funds</h2>
                            <p>Your Wallet Address: {address}</p>
                            <input
                                type="number"
                                placeholder="Amount to Simulate Receiving"
                                value={receiveAmount}
                                onChange={(e) => setReceiveAmount(e.target.value)}
                            />
                            <button onClick={receiveFunds}>Receive</button>
                        </div>
                    )}

                    {view === 'transactions' && (
                        <div className="transaction-history">
                            <h2>Transaction History</h2>
                            {transactions.length > 0 ? (
                                <ul>
                                    {transactions.map((tx, index) => (
                                        <li key={index}>
                                            From: {tx.sender}<br />
                                            To: {tx.recipient}<br />
                                            Amount: {tx.amount}<br />
                                            Timestamp: {tx.timestamp}
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>No transactions yet.</p>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

export default App;
