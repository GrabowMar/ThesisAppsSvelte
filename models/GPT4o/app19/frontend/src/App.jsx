import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  // App state
  const [balance, setBalance] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");
  const [recipient, setRecipient] = useState("");
  const [amount, setAmount] = useState("");

  // Fetch balance on load
  useEffect(() => {
    fetch("http://localhost:5277/api/get_balance?user_id=user1")
      .then((response) => response.json())
      .then((data) => {
        if (data.balance !== undefined) {
          setBalance(data.balance);
        } else {
          setError(data.error || "Unknown error.");
        }
      })
      .catch((err) => setError("Failed to fetch balance"));
  }, []);

  // Fetch transaction history
  useEffect(() => {
    fetch("http://localhost:5277/api/transaction_history?user_id=user1")
      .then((response) => response.json())
      .then((data) => {
        if (data.transactions) {
          setTransactions(data.transactions);
        } else {
          setError(data.error || "Unknown error.");
        }
      })
      .catch((err) => setError("Failed to fetch transaction history"));
  }, []);

  // Send funds handler
  const sendFunds = () => {
    fetch("http://localhost:5277/api/send_funds", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sender_id: "user1",
        recipient: recipient,
        amount: parseFloat(amount)
      })
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setBalance((prev) => prev - amount);
          setTransactions((prev) => [...prev, data.transaction]);
          setRecipient("");
          setAmount("");
          setError(""); // Clear errors on success
        }
      })
      .catch((err) => setError("Failed to process transaction"));
  };

  return (
    <div className="app">
      <h1>Crypto Wallet</h1>
      <h2>Balance: {balance !== null ? `${balance} Crypto` : "Loading..."}</h2>
      {error && <p className="error">{error}</p>}

      <div className="transaction">
        <h3>Send Funds</h3>
        <input
          type="text"
          placeholder="Recipient Address"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
        />
        <input
          type="number"
          placeholder="Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
        <button onClick={sendFunds}>Send</button>
      </div>

      <div className="history">
        <h3>Transaction History</h3>
        <ul>
          {transactions.map((tx) => (
            <li key={tx.transaction_id}>
              <strong>ID:</strong> {tx.transaction_id} | <strong>To:</strong> {tx.recipient} | <strong>Amount:</strong> {tx.amount}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Mount the App component
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
