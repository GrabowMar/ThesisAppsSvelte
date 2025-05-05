import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement } from 'chart.js';
import { Pie, Bar, Line } from 'react-chartjs-2';
import './App.css';

// Register ChartJS components
ChartJS.register(
  ArcElement, Tooltip, Legend, CategoryScale, 
  LinearScale, BarElement, PointElement, LineElement
);

const App = () => {
  // State management
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [goals, setGoals] = useState([]);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    type: 'expense',
    amount: '',
    category: '',
    description: '',
    date: new Date().toISOString().split('T')[0],
    name: '',
    target_amount: '',
    current_amount: '',
    target_date: new Date().toISOString().split('T')[0],
    month: new Date().toISOString().substring(0, 7)
  });
  const [summary, setSummary] = useState({
    balance: 0,
    income: 0,
    expenses: 0,
    monthly_summary: {}
  });
  const [categories, setCategories] = useState([]);

  // Fetch data on mount
  useEffect(() => {
    if (isLoggedIn) {
      fetchData();
    }
  }, [isLoggedIn]);

  const fetchData = async () => {
    try {
      const [transRes, budgetsRes, goalsRes, summaryRes, catRes] = await Promise.all([
        fetch('/api/transactions'),
        fetch('/api/budgets'),
        fetch('/api/goals'),
        fetch('/api/summary'),
        fetch('/api/categories')
      ]);
      
      setTransactions(await transRes.json());
      setBudgets(await budgetsRes.json());
      setGoals(await goalsRes.json());
      setSummary(await summaryRes.json());
      setCategories(await catRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  // Authentication handlers
  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        setIsLoggedIn(true);
        setUser(data.user);
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password,
          email: formData.email
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        alert('Registration successful! Please login.');
        setActiveTab('login');
        setFormData({...formData, password: ''});
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Registration error:', error);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUser(null);
    setActiveTab('login');
  };

  // Transaction handlers
  const addTransaction = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/transactions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: formData.type,
          amount: parseFloat(formData.amount),
          category: formData.category,
          description: formData.description,
          date: formData.date
        }),
      });
      
      const newTransaction = await response.json();
      setTransactions([...transactions, newTransaction]);
      setFormData({...formData, amount: '', description: ''});
      fetchData(); // Refresh summary
    } catch (error) {
      console.error('Error adding transaction:', error);
    }
  };

  const deleteTransaction = async (id) => {
    try {
      await fetch(`/api/transactions/${id}`, {
        method: 'DELETE'
      });
      setTransactions(transactions.filter(t => t.id !== id));
      fetchData(); // Refresh summary
    } catch (error) {
      console.error('Error deleting transaction:', error);
    }
  };

  // Budget handlers
  const addBudget = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/budgets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: formData.category,
          amount: parseFloat(formData.amount),
          month: formData.month
        }),
      });
      
      const newBudget = await response.json();
      setBudgets([...budgets, newBudget]);
      setFormData({...formData, amount: ''});
    } catch (error) {
      console.error('Error adding budget:', error);
    }
  };

  const deleteBudget = async (id) => {
    try {
      await fetch(`/api/budgets/${id}`, {
        method: 'DELETE'
      });
      setBudgets(budgets.filter(b => b.id !== id));
    } catch (error) {
      console.error('Error deleting budget:', error);
    }
  };

  // Goal handlers
  const addGoal = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/goals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          target_amount: parseFloat(formData.target_amount),
          current_amount: parseFloat(formData.current_amount || 0),
          target_date: formData.target_date
        }),
      });
      
      const newGoal = await response.json();
      setGoals([...goals, newGoal]);
      setFormData({...formData, name: '', target_amount: '', current_amount: ''});
    } catch (error) {
      console.error('Error adding goal:', error);
    }
  };

  const deleteGoal = async (id) => {
    try {
      await fetch(`/api/goals/${id}`, {
        method: 'DELETE'
      });
      setGoals(goals.filter(g => g.id !== id));
    } catch (error) {
      console.error('Error deleting goal:', error);
    }
  };

  // Form change handler
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  // Data for charts
  const expenseData = {
    labels: categories,
    datasets: [{
      label: 'Expenses by Category',
      data: categories.map(cat => 
        transactions
          .filter(t => t.type === 'expense' && t.category === cat)
          .reduce((sum, t) => sum + t.amount, 0)
      ),
      backgroundColor: [
        'rgba(255, 99, 132, 0.7)',
        'rgba(54, 162, 235, 0.7)',
        'rgba(255, 206, 86, 0.7)',
        'rgba(75, 192, 192, 0.7)',
        'rgba(153, 102, 255, 0.7)',
        'rgba(255, 159, 64, 0.7)',
        'rgba(199, 199, 199, 0.7)',
        'rgba(83, 102, 255, 0.7)',
        'rgba(40, 159, 64, 0.7)',
        'rgba(210, 99, 132, 0.7)'
      ],
      borderWidth: 1
    }]
  };

  const monthlyData = {
    labels: Object.keys(summary.monthly_summary),
    datasets: [
      {
        label: 'Income',
        data: Object.values(summary.monthly_summary).map(m => m.income),
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
      },
      {
        label: 'Expenses',
        data: Object.values(summary.monthly_summary).map(m => m.expenses),
        backgroundColor: 'rgba(255, 99, 132, 0.7)',
      }
    ]
  };

  // Tab rendering
  const renderTab = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="dashboard">
            <div className="summary-cards">
              <div className="card">
                <h3>Current Balance</h3>
                <p className={summary.balance >= 0 ? 'positive' : 'negative'}>
                  ${summary.balance.toFixed(2)}
                </p>
              </div>
              <div className="card">
                <h3>Total Income</h3>
                <p className="positive">${summary.income.toFixed(2)}</p>
              </div>
              <div className="card">
                <h3>Total Expenses</h3>
                <p className="negative">${summary.expenses.toFixed(2)}</p>
              </div>
            </div>

            <div className="charts">
              <div className="chart-container">
                <h3>Expense Breakdown</h3>
                <Pie data={expenseData} />
              </div>
              <div className="chart-container">
                <h3>Monthly Income vs Expenses</h3>
                <Bar data={monthlyData} />
              </div>
            </div>

            <div className="recent-transactions">
              <h3>Recent Transactions</h3>
              <table>
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.slice(0, 5).map((t, i) => (
                    <tr key={i}>
                      <td>{t.type}</td>
                      <td className={t.type === 'income' ? 'positive' : 'negative'}>
                        ${t.amount.toFixed(2)}
                      </td>
                      <td>{t.category}</td>
                      <td>{t.description}</td>
                      <td>{t.date}</td>
                      <td>
                        <button onClick={() => deleteTransaction(t.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      
      case 'transactions':
        return (
          <div className="transactions">
            <h2>Transaction Management</h2>
            
            <form onSubmit={addTransaction} className="transaction-form">
              <h3>Add New Transaction</h3>
              <div className="form-group">
                <label>Type:</label>
                <select name="type" value={formData.type} onChange={handleChange} required>
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Amount:</label>
                <input 
                  type="number" 
                  name="amount" 
                  value={formData.amount} 
                  onChange={handleChange} 
                  step="0.01" 
                  min="0"
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Category:</label>
                <select name="category" value={formData.category} onChange={handleChange} required>
                  <option value="">Select a category</option>
                  {categories.map((cat, i) => (
                    <option key={i} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Description:</label>
                <input 
                  type="text" 
                  name="description" 
                  value={formData.description} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Date:</label>
                <input 
                  type="date" 
                  name="date" 
                  value={formData.date} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <button type="submit">Add Transaction</button>
            </form>
            
            <div className="transaction-list">
              <h3>All Transactions</h3>
              {transactions.length === 0 ? (
                <p>No transactions recorded yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Category</th>
                      <th>Description</th>
                      <th>Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((t, i) => (
                      <tr key={i}>
                        <td>{t.type}</td>
                        <td className={t.type === 'income' ? 'positive' : 'negative'}>
                           $ {t.amount.toFixed(2)}
                        </td>
                        <td>{t.category}</td>
                        <td>{t.description}</td>
                        <td>{t.date}</td>
                        <td>
                          <button onClick={() => deleteTransaction(t.id)}>Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );
      
      case 'budgets':
        return (
          <div className="budgets">
            <h2>Budget Management</h2>
            
            <form onSubmit={addBudget} className="budget-form">
              <h3>Create New Budget</h3>
              <div className="form-group">
                <label>Category:</label>
                <select name="category" value={formData.category} onChange={handleChange} required>
                  <option value="">Select a category</option>
                  {categories.map((cat, i) => (
                    <option key={i} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Amount ( $ ):</label>
                <input 
                  type="number" 
                  name="amount" 
                  value={formData.amount} 
                  onChange={handleChange} 
                  step="0.01" 
                  min="0"
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Month:</label>
                <input 
                  type="month" 
                  name="month" 
                  value={formData.month} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <button type="submit">Create Budget</button>
            </form>
            
            <div className="budget-list">
              <h3>Current Budgets</h3>
              {budgets.length === 0 ? (
                <p>No budgets created yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Amount</th>
                      <th>Month</th>
                      <th>Spent</th>
                      <th>Remaining</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {budgets.map((b, i) => {
                      const spent = transactions
                        .filter(t => 
                          t.type === 'expense' && 
                          t.category === b.category && 
                          t.date.startsWith(b.month)
                        )
                        .reduce((sum, t) => sum + t.amount, 0);
                      const remaining = b.amount - spent;
                      
                      return (
                        <tr key={i}>
                          <td>{b.category}</td>
                          <td>${b.amount.toFixed(2)}</td>
                          <td>{b.month}</td>
                          <td className="negative">${spent.toFixed(2)}</td>
                          <td className={remaining >= 0 ? 'positive' : 'negative'}>
                             $ {remaining.toFixed(2)}
                          </td>
                          <td>
                            <button onClick={() => deleteBudget(b.id)}>Delete</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );
      
      case 'goals':
        return (
          <div className="goals">
            <h2>Financial Goals</h2>
            
            <form onSubmit={addGoal} className="goal-form">
              <h3>Create New Goal</h3>
              <div className="form-group">
                <label>Goal Name:</label>
                <input 
                  type="text" 
                  name="name" 
                  value={formData.name} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Target Amount ( $ ):</label>
                <input 
                  type="number" 
                  name="target_amount" 
                  value={formData.target_amount} 
                  onChange={handleChange} 
                  step="0.01" 
                  min="0"
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Current Amount ($):</label>
                <input 
                  type="number" 
                  name="current_amount" 
                  value={formData.current_amount} 
                  onChange={handleChange} 
                  step="0.01" 
                  min="0"
                />
              </div>
              
              <div className="form-group">
                <label>Target Date:</label>
                <input 
                  type="date" 
                  name="target_date" 
                  value={formData.target_date} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <button type="submit">Create Goal</button>
            </form>
            
            <div className="goal-list">
              <h3>Your Goals</h3>
              {goals.length === 0 ? (
                <p>No goals set yet.</p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Target Amount</th>
                      <th>Current Amount</th>
                      <th>Progress</th>
                      <th>Target Date</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {goals.map((g, i) => {
                      const progress = (g.current_amount / g.target_amount) * 100;
                      const status = 
                        progress >= 100 ? 'Completed' : 
                        new Date(g.target_date) < new Date() ? 'Overdue' : 'In Progress';
                      
                      return (
                        <tr key={i}>
                          <td>{g.name}</td>
                          <td>${g.target_amount.toFixed(2)}</td>
                          <td>${g.current_amount.toFixed(2)}</td>
                          <td>
                            <div className="progress-bar">
                              <div 
                                className="progress-fill" 
                                style={{ width: `${Math.min(progress, 100)}%` }}
                              ></div>
                              <span>{Math.round(progress)}%</span>
                            </div>
                          </td>
                          <td>{g.target_date}</td>
                          <td className={
                            status === 'Completed' ? 'positive' :
                            status === 'Overdue' ? 'negative' : ''
                          }>
                            {status}
                          </td>
                          <td>
                            <button onClick={() => deleteGoal(g.id)}>Delete</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        );
      
      case 'login':
        return (
          <div className="auth-form">
            <h2>Login</h2>
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label>Username:</label>
                <input 
                  type="text" 
                  name="username" 
                  value={formData.username} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Password:</label>
                <input 
                  type="password" 
                  name="password" 
                  value={formData.password} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <button type="submit">Login</button>
              <p>
                Don't have an account?{' '}
                <button type="button" onClick={() => setActiveTab('register')}>
                  Register
                </button>
              </p>
            </form>
          </div>
        );
      
      case 'register':
        return (
          <div className="auth-form">
            <h2>Register</h2>
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label>Username:</label>
                <input 
                  type="text" 
                  name="username" 
                  value={formData.username} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Password:</label>
                <input 
                  type="password" 
                  name="password" 
                  value={formData.password} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <div className="form-group">
                <label>Email:</label>
                <input 
                  type="email" 
                  name="email" 
                  value={formData.email} 
                  onChange={handleChange} 
                  required 
                />
              </div>
              
              <button type="submit">Register</button>
              <p>
                Already have an account?{' '}
                <button type="button" onClick={() => setActiveTab('login')}>
                  Login
                </button>
              </p>
            </form>
          </div>
        );
      
      default:
        return null;
    }
  };

  // Main render
  return (
    <div className="app">
      {isLoggedIn ? (
        <>
          <header className="app-header">
            <h1>Personal Finance Tracker</h1>
            <div className="user-info">
              <span>Welcome, {user?.username}</span>
              <button onClick={handleLogout}>Logout</button>
            </div>
          </header>
          
          <nav className="main-nav">
            <button 
              className={activeTab === 'dashboard' ? 'active' : ''}
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={activeTab === 'transactions' ? 'active' : ''}
              onClick={() => setActiveTab('transactions')}
            >
              Transactions
            </button>
            <button 
              className={activeTab === 'budgets' ? 'active' : ''}
              onClick={() => setActiveTab('budgets')}
            >
              Budgets
            </button>
            <button 
              className={activeTab === 'goals' ? 'active' : ''}
              onClick={() => setActiveTab('goals')}
            >
              Goals
            </button>
          </nav>
          
          <main className="main-content">
            {renderTab()}
          </main>
        </>
      ) : (
        <div className="auth-container">
          {renderTab()}
        </div>
      )}
    </div>
  );
};

// Mount the app
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
