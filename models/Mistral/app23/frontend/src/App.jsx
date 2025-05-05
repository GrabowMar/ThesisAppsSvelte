import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// UI Components
const Navbar = () => (
  <nav>
    <ul>
      <li><Link to="/">Home</Link></li>
      <li><Link to="/transactions">Transactions</Link></li>
      <li><Link to="/budgets">Budgets</Link></li>
      <li><Link to="/goals">Goals</Link></li>
    </ul>
  </nav>
);

const Home = () => <h1>Welcome to your Personal Finance Tracker</h1>;

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [form, setForm] = useState({ type: '', amount: '', category: '' });

  useEffect(() => {
    axios.get('/api/transactions').then(response => setTransactions(response.data));
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/transactions', form).then(response => {
      setTransactions([...transactions, response.data]);
      setForm({ type: '', amount: '', category: '' });
    });
  };

  return (
    <div>
      <h1>Transactions</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="type" placeholder="Type" value={form.type} onChange={handleChange} required />
        <input type="number" name="amount" placeholder="Amount" value={form.amount} onChange={handleChange} required />
        <input type="text" name="category" placeholder="Category" value={form.category} onChange={handleChange} required />
        <button type="submit">Add Transaction</button>
      </form>
      <ul>
        {transactions.map(transaction => (
          <li key={transaction.id}>{transaction.type} - ${transaction.amount} - {transaction.category}</li>
        ))}
      </ul>
    </div>
  );
};

const Budgets = () => {
  const [budgets, setBudgets] = useState([]);
  const [form, setForm] = useState({ category: '', amount: '' });

  useEffect(() => {
    axios.get('/api/budgets').then(response => setBudgets(response.data));
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/budgets', form).then(response => {
      setBudgets([...budgets, response.data]);
      setForm({ category: '', amount: '' });
    });
  };

  return (
    <div>
      <h1>Budgets</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="category" placeholder="Category" value={form.category} onChange={handleChange} required />
        <input type="number" name="amount" placeholder="Amount" value={form.amount} onChange={handleChange} required />
        <button type="submit">Add Budget</button>
      </form>
      <ul>
        {budgets.map(budget => (
          <li key={budget.id}>{budget.category} - ${budget.amount}</li>
        ))}
      </ul>
    </div>
  );
};

const Goals = () => {
  const [goals, setGoals] = useState([]);
  const [form, setForm] = useState({ name: '', amount: '', deadline: '' });

  useEffect(() => {
    axios.get('/api/goals').then(response => setGoals(response.data));
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post('/api/goals', form).then(response => {
      setGoals([...goals, response.data]);
      setForm({ name: '', amount: '', deadline: '' });
    });
  };

  return (
    <div>
      <h1>Goals</h1>
      <form onSubmit={handleSubmit}>
        <input type="text" name="name" placeholder="Goal Name" value={form.name} onChange={handleChange} required />
        <input type="number" name="amount" placeholder="Amount" value={form.amount} onChange={handleChange} required />
        <input type="date" name="deadline" value={form.deadline} onChange={handleChange} required />
        <button type="submit">Add Goal</button>
      </form>
      <ul>
        {goals.map(goal => (
          <li key={goal.id}>{goal.name} - ${goal.amount} - {new Date(goal.deadline).toLocaleDateString()}</li>
        ))}
      </ul>
    </div>
  );
};

const App = () => (
  <Router>
    <Navbar />
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/transactions" element={<Transactions />} />
      <Route path="/budgets" element={<Budgets />} />
      <Route path="/goals" element={<Goals />} />
    </Routes>
  </Router>
);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
