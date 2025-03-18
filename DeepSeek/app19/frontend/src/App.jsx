import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [balance, setBalance] = useState(0);
  const [transactions, setTransactions] = useState([]);
  const [address, setAddress] = useState("");
  const [sendAmount, setSendAmount] = useState("");
  const [sendTo, setSendTo] = useState("");

  // Fetch user balance and address on mount
  useEffect(() => {
    fetch("http://localhost:5197/api/balance")
      .then((response) => response.json())
      .then((data) => setBalance(data.balance))
      .catch((error) => console.error("Error fetching balance:", error));

    fetch("http://localhost:5197/api/address")
      .then((response) => response.json())
      .then((data) => setAddress(data.address))
      .catch((error) => console.error("Error fetching address:", error));

    fetch("http://localhost:5197/api/transactions")
      .then((response) => response.json())
      .then((data) => setTransactions(data.transactions))
      .catch((error) => console.error("Error fetching transactions:", error));
  }, []);

  // Handle send transaction
  const handleSend = async () => {
    if (!sendAmount || !sendTo) {
      alert("Please fill in all fields.");
      return;
    }

    const response = await fetch("http://localhost:5197/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: parseFloat(sendAmount), to: sendTo }),
    });

    const data = await response.json();
    if (response.ok) {
      alert("Transaction successful!");
      setBalance(data.balance);
      setSendAmount("");
      setSendTo("");
      // Refresh transactions
      fetch("http://localhost:5197/api/transactions")
        .then((response) => response.json())
        .then((data) => setTransactions(data.transactions));
    } else {
      alert(`Error: ${data.error}`);
    }
  };

  return (
    <div className="app-container">
      <h1>Crypto Wallet</h1>
      <div className="info-section">
        <p>Your Address: <strong>{address}</strong></p>
        <p>Balance: <strong>{balance.toFixed(2)}</strong></p>
      </div>
      <div className="send-section">
        <h2>Send Crypto</h2>
        <input
          type="number"
          placeholder="Amount"
          value={sendAmount}
          onChange={(e) => setSendAmount(e.target.value)}
        />
        <input
          type="text"
          placeholder="Recipient Address"
          value={sendTo}
          onChange={(e) => setSendTo(e.target.value)}
        />
        <button onClick={handleSend}>Send</button>
      </div>
      <div className="transactions-section">
        <h2>Transaction History</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Type</th>
              <th>Amount</th>
              <th>To/From</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx) => (
              <tr key={tx.id}>
                <td>{tx.id}</td>
                <td>{tx.type}</td>
                <td>{tx.amount.toFixed(2)}</td>
                <td>{tx.type === "send" ? tx.to : tx.from}</td>
                <td>{tx.timestamp}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Mount the app
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
