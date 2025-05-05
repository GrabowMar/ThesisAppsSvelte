import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
  const [token, setToken] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [goals, setGoals] = useState([]);
  const [reports, setReports] = useState({});

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    try {
      const response = await axios.post('/api/login', { username, password });
      setToken(response.data.token);
      localStorage.setItem('token', response.data.token);
    } catch (error) {
      console.error(error);
    }
  };

  const handleTransactionSubmit = async (e) => {
    e.preventDefault();
    const amount = e.target.amount.value;
    const category = e.target.category.value;
    const type = e.target.type.value;
    try {
      const response = await axios.post('/api/transactions', { amount, category, type }, {
        headers: { Authorization: token }
      });
      setTransactions([...transactions, response.data]);
    } catch (error) {
      console.error(error);
    }
  };

  const handleBudgetSubmit = async (e) => {
    e.preventDefault();
    const category = e.target.category.value;
    const limit = e.target.limit.value;
    try {
      const response = await axios.post('/api/budgets', { category, limit }, {
        headers: { Authorization: token }
      });
      setBudgets([...budgets, response.data]);
    } catch (error) {
      console.error(error);
    }
  };

  const handleGoalSubmit = async (e) => {
    e.preventDefault();
    const target = e.target.target.value;
    try {
      const response = await axios.post('/api/goals', { target }, {
        headers: { Authorization: token }
      });
      setGoals([...goals, response.data]);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchData = async () => {
    try {
      const transactionsResponse = await axios.get('/api/transactions', {
        headers: { Authorization: token }
      });
      setTransactions(transactionsResponse.data);

      const budgetsResponse = await axios.get('/api/budgets', {
        headers: { Authorization: token }
      });
      setBudgets(budgetsResponse.data);

      const goalsResponse = await axios.get('/api/goals', {
        headers: { Authorization: token }
      });
      setGoals(goalsResponse.data);

      const reportsResponse = await axios.get('/api/reports', {
        headers: { Authorization: token }
      });
      setReports(reportsResponse.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [token]);

  return (
    <div>
      {!token && (
        <form onSubmit={handleLogin}>
          <input type="text" name="username" placeholder="Username" />
          <input type="password" name="password" placeholder="Password" />
          <button type="submit">Login</button>
        </form>
      )}
      {token && (
        <div>
          <h1>Transactions</h1>
          <form onSubmit={handleTransactionSubmit}>
            <input type="number" name="amount" placeholder="Amount" />
            <input type="text" name="category" placeholder="Category" />
            <select name="type">
              <option value="income">Income</option>
              <option value="expense">Expense</option>
            </select>
            <button type="submit">Add Transaction</button>
          </form>
          <ul>
            {transactions.map((transaction) => (
              <li key={transaction.id}>
                {transaction.date} - {transaction.amount} ({transaction.category})
              </li>
            ))}
          </ul>

          <h1>Budgets</h1>
          <form onSubmit={handleBudgetSubmit}>
            <input type="text" name="category" placeholder="Category" />
            <input type="number" name="limit" placeholder="Limit" />
            <button type="submit">Add Budget</button>
          </form>
          <ul>
            {budgets.map((budget) => (
              <li key={budget.id}>
                {budget.category} - {budget.limit}
              </li>
            ))}
          </ul>

          <h1>Goals</h1>
          <form onSubmit={handleGoalSubmit}>
            <input type="number" name="target" placeholder="Target" />
            <button type="submit">Add Goal</button>
          </form>
          <ul>
            {goals.map((goal) => (
              <li key={goal.id}>
                {goal.target}
              </li>
            ))}
          </ul>

          <h1>Reports</h1>
          <p>Income: {reports.income}</p>
          <p>Expenses: {reports.expenses}</p>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
