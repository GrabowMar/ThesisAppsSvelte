import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import axios from 'axios';

// Set up axios defaults
axios.defaults.baseURL = 'http://localhost:5997/api';

// Components
const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/login', { username, password });
      if (response.status === 200) {
        localStorage.setItem('isAuthenticated', 'true');
        window.location.href = '/dashboard';
      }
    } catch (error) {
      setError('Invalid credentials');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleLogin}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/register', { username, password });
      if (response.status === 201) {
        window.location.href = '/login';
      }
    } catch (error) {
      setError('Registration failed. Username may already exist.');
    }
  };

  return (
    <div>
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleRegister}>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
        />
        <button type="submit">Register</button>
      </form>
    </div>
  );
};

const Dashboard = () => {
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [newItem, setNewItem] = useState({
    name: '',
    description: '',
    quantity: 0,
    category_id: 1,
  });
  const [newCategory, setNewCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [stockAlerts, setStockAlerts] = useState([]);

  useEffect(() => {
    fetchItems();
    fetchCategories();
    fetchStockAlerts();
  }, []);

  const fetchItems = async () => {
    try {
      const response = await axios.get('/items');
      setItems(response.data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchStockAlerts = async () => {
    try {
      const response = await axios.get('/stock_alerts');
      setStockAlerts(response.data.low_stock_items);
    } catch (error) {
      console.error('Error fetching stock alerts:', error);
    }
  };

  const handleCreateItem = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/items', newItem);
      fetchItems();
      setNewItem({ name: '', description: '', quantity: 0, category_id: 1 });
    } catch (error) {
      console.error('Error creating item:', error);
    }
  };

  const handleUpdateItem = async (item) => {
    try {
      await axios.put(`/items/${item.id}`, item);
      fetchItems();
    } catch (error) {
      console.error('Error updating item:', error);
    }
  };

  const handleDeleteItem = async (itemId) => {
    try {
      await axios.delete(`/items/${itemId}`);
      fetchItems();
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/categories', { name: newCategory });
      fetchCategories();
      setNewCategory('');
    } catch (error) {
      console.error('Error creating category:', error);
    }
  };

  const handleSearch = async () => {
    try {
      const response = await axios.get(`/search?q=${searchQuery}`);
      setItems(response.data);
    } catch (error) {
      console.error('Error searching items:', error);
    }
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <div>
        <h3>Stock Alerts</h3>
        {stockAlerts.length > 0 ? (
          <ul>
            {stockAlerts.map((itemId) => (
              <li key={itemId}>Item ID: {itemId}</li>
            ))}
          </ul>
        ) : (
          <p>No stock alerts</p>
        )}
      </div>
      <div>
        <h3>Search Items</h3>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search items"
        />
        <button onClick={handleSearch}>Search</button>
      </div>
      <div>
        <h3>Create New Item</h3>
        <form onSubmit={handleCreateItem}>
          <input
            type="text"
            value={newItem.name}
            onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
            placeholder="Name"
            required
          />
          <input
            type="text"
            value={newItem.description}
            onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
            placeholder="Description"
          />
          <input
            type="number"
            value={newItem.quantity}
            onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) })}
            placeholder="Quantity"
            required
          />
          <select
            value={newItem.category_id}
            onChange={(e) => setNewItem({ ...newItem, category_id: parseInt(e.target.value) })}
            required
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <button type="submit">Create Item</button>
        </form>
      </div>
      <div>
        <h3>Create New Category</h3>
        <form onSubmit={handleCreateCategory}>
          <input
            type="text"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            placeholder="Category Name"
            required
          />
          <button type="submit">Create Category</button>
        </form>
      </div>
      <div>
        <h3>Inventory</h3>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Description</th>
              <th>Quantity</th>
              <th>Category</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.name}</td>
                <td>{item.description}</td>
                <td>{item.quantity}</td>
                <td>{item.category.name}</td>
                <td>
                  <button onClick={() => handleUpdateItem({ ...item, quantity: item.quantity + 1 })}>
                    +
                  </button>
                  <button onClick={() => handleUpdateItem({ ...item, quantity: item.quantity - 1 })}>
                    -
                  </button>
                  <button onClick={() => handleDeleteItem(item.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const PrivateRoute = ({ children }) => {
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
