import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({});
  const [goals, setGoals] = useState([]);
  const [formData, setFormData] = useState({
    id: "",
    description: "",
    amount: "",
    category: "",
    type: "income", // Default to income
  });

  // Fetch Transactions and Goals
  const fetchData = async () => {
    try {
      const txnResponse = await fetch("/api/transactions");
      const txnData = await txnResponse.json();
      setTransactions(txnData.data);
      setSummary(txnData.summary);

      const goalResponse = await fetch("/api/goals");
      const goalData = await goalResponse.json();
      setGoals(goalData.data);
    } catch (error) {
      console.error("Error fetching data", error);
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        fetchData(); // Refresh data
        setFormData({ id: "", description: "", amount: "", category: "", type: "income" }); // Reset form
      } else {
        console.error("Failed to add transaction");
      }
    } catch (error) {
      console.error("Error submitting form", error);
    }
  };

  // Fetch Data on Mount
  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <h1>Personal Finance Tracker</h1>
      </header>
      <main className="main">
        <section className="summary">
          <h2>Budget Summary</h2>
          <p>Income: ${summary.income || 0}</p>
          <p>Expenses: ${summary.expenses || 0}</p>
          <p>Balance: ${summary.balance || 0}</p>
        </section>
        <section className="transactions">
          <h2>Transactions</h2>
          <ul>
            {transactions.map((txn) => (
              <li key={txn.id}>
                {txn.description} - ${txn.amount} ({txn.category} - {txn.type})
              </li>
            ))}
          </ul>
        </section>
        <section className="add-transaction">
          <h2>Add Transaction</h2>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="ID"
              value={formData.id}
              onChange={(e) => setFormData({ ...formData, id: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
            <input
              type="number"
              placeholder="Amount"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              required
            />
            <select
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
            >
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
            <button type="submit">Add Transaction</button>
          </form>
        </section>
        <section className="goals">
          <h2>Goals</h2>
          <ul>
            {goals.map((goal, index) => (
              <li key={index}>
                {goal.name} - Target: ${goal.targetAmount}
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
