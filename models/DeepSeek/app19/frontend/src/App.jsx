// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// 2. App Component
const App = () => {
  const [balance, setBalance] = useState(0);
  const [address, setAddress] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [page, setPage] = useState('dashboard'); // Multipage routing
  const [receiver, setReceiver] = useState('');
  const [amount, setAmount] = useState('');

  // 3. Fetch Balance and Transactions on Mount
  useEffect(() => {
    fetch('/api/balance')
      .then(res => res.json())
      .then(data => {
        setBalance(data.balance);
        setAddress(data.address);
      });

    fetch('/api/transactions')
      .then(res => res.json())
      .then(data => setTransactions(data));
  }, []);

  // 4. Handle Send Transaction
  const handleSend = async () => {
    const response = await fetch('/api/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ receiver, amount: parseFloat(amount) })
    });

    if (response.ok) {
      const data = await response.json();
      alert(`Transaction successful! TX ID: ${data.tx_id}`);
      window.location.reload(); // Refresh data
    } else {
      alert('Transaction failed. Please check the details.');
    }
  };

  // 5. Render Page
  return (
    <main>
      <nav>
        <button onClick={() => setPage('dashboard')}>Dashboard</button>
        <button onClick={() => setPage('send')}>Send Crypto</button>
      </nav>

      {page === 'dashboard' && (
        <div>
          <h1>Dashboard</h1>
          <p>Balance: {balance} ETH</p>
          <p>Address: {address}</p>
          <h2>Transaction History</h2>
          <ul>
            {transactions.map(tx => (
              <li key={tx.tx_id}>
                {tx.sender} ➡️ {tx.receiver} - {tx.amount} ETH
              </li>
            ))}
          </ul>
        </div>
      )}

      {page === 'send' && (
        <div>
          <h1>Send Crypto</h1>
          <input
            type="text"
            placeholder="Receiver Address"
            value={receiver}
            onChange={(e) => setReceiver(e.target.value)}
          />
          <input
            type="number"
            placeholder="Amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
          <button onClick={handleSend}>Send</button>
        </div>
      )}
    </main>
  );
};

// 6. Mount App
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
