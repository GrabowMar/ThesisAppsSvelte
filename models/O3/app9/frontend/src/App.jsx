import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Backend API base URL (using Vite proxy, the fetch calls can use '/api/...')
const API_URL = '/api';

const App = () => {
  // State to manage page routing: "home", "add", "edit", "login", etc.
  const [page, setPage] = useState("home");
  // Inventory items
  const [items, setItems] = useState([]);
  // Alert messages
  const [alert, setAlert] = useState(null);
  // Form state for add/edit
  const [formData, setFormData] = useState({
    id: null,
    name: '',
    category: '',
    quantity: '',
    threshold: ''
  });
  // Search filters
  const [filters, setFilters] = useState({ search: '', category: '' });
  // For edit mode toggle
  const [isEdit, setIsEdit] = useState(false);

  // Fetch items list based on filters
  const fetchItems = async () => {
    try {
      let url = `${API_URL}/items?`;
      if (filters.search) url += `search=${filters.search}&`;
      if (filters.category) url += `category=${filters.category}&`;
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch items");
      const data = await res.json();
      setItems(data);
    } catch (error) {
      setAlert({ type: 'error', message: error.message });
    }
  };

  useEffect(() => {
    if (page === "home") {
      fetchItems();
    }
  }, [page, filters]);

  // Reset form on page change
  const resetForm = () => {
    setFormData({ id: null, name: '', category: '', quantity: '', threshold: '' });
    setIsEdit(false);
  };

  // Change page handler
  const navigate = (p) => {
    setAlert(null);
    resetForm();
    setPage(p);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value
    }));
  };

  // Submit for add and edit
  const handleSubmit = async (e) => {
    e.preventDefault();
    // Validate fields
    if (!formData.name || !formData.category || formData.quantity === '') {
      setAlert({ type: 'error', message: "Please fill in all required fields." });
      return;
    }
    try {
      let res;
      const payload = {
        name: formData.name,
        category: formData.category,
        quantity: parseInt(formData.quantity),
        threshold: formData.threshold ? parseInt(formData.threshold) : 0
      };

      if (isEdit) {
        res = await fetch(`${API_URL}/items/${formData.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetch(`${API_URL}/items`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Operation failed");
      }
      setAlert({ type: 'success', message: isEdit ? "Item updated successfully" : "Item added successfully" });
      navigate("home");
    } catch (error) {
      setAlert({ type: 'error', message: error.message });
    }
  };

  // Delete an item
  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    try {
      const res = await fetch(`${API_URL}/items/${id}`, {
        method: 'DELETE'
      });
      if (!res.ok) throw new Error("Delete failed");
      setAlert({ type: 'success', message: "Item deleted successfully" });
      fetchItems();
    } catch (error) {
      setAlert({ type: 'error', message: error.message });
    }
  };

  // Set form for editing an item
  const startEdit = (item) => {
    setFormData({
      id: item.id,
      name: item.name,
      category: item.category,
      quantity: item.quantity,
      threshold: item.threshold,
    });
    setIsEdit(true);
    setPage("add");
  };

  // Render Alert if present
  const Alert = ({ type, message }) => (
    <div className={`alert ${type}`}>{message}</div>
  );

  // Inventory Table component
  const InventoryList = () => (
    <div>
      <h2>Inventory Items</h2>
      <div className="filters">
        <input 
          type="text" 
          placeholder="Search by name" 
          value={filters.search} 
          onChange={e => setFilters({...filters, search: e.target.value})} 
        />
        <input 
          type="text" 
          placeholder="Filter by category" 
          value={filters.category} 
          onChange={e => setFilters({...filters, category: e.target.value})} 
        />
        <button onClick={fetchItems}>Apply Filters</button>
      </div>
      {items.length === 0 ? (
        <p>No items found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Category</th>
              <th>Quantity</th>
              <th>Threshold</th>
              <th>Alert</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => {
              const lowStock = item.quantity < item.threshold;
              return (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.name}</td>
                  <td>{item.category}</td>
                  <td>{item.quantity}</td>
                  <td>{item.threshold}</td>
                  <td>{lowStock ? <span className="alert-text">Low Stock</span> : "OK"}</td>
                  <td>
                    <button onClick={() => startEdit(item)}>Edit</button>
                    <button onClick={() => handleDelete(item.id)}>Delete</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );

  // Form component for adding or editing an item
  const ItemForm = () => (
    <div>
      <h2>{isEdit ? "Edit Item" : "Add New Item"}</h2>
      <form onSubmit={handleSubmit}>
        <label>Name: <span className="required">*</span>
          <input type="text" name="name" value={formData.name} onChange={handleFormChange} required />
        </label>
        <label>Category: <span className="required">*</span>
          <input type="text" name="category" value={formData.category} onChange={handleFormChange} required />
        </label>
        <label>Quantity: <span className="required">*</span>
          <input type="number" name="quantity" value={formData.quantity} onChange={handleFormChange} required />
        </label>
        <label>Threshold:
          <input type="number" name="threshold" value={formData.threshold} onChange={handleFormChange} />
        </label>
        <button type="submit">{isEdit ? "Update" : "Add"}</button>
        <button type="button" onClick={() => navigate("home")}>Cancel</button>
      </form>
    </div>
  );

  // A simple Login component example (dummy)
  const Login = () => {
    const [loginData, setLoginData] = useState({ username: '', password: '' });

    const handleLoginChange = (e) => {
      setLoginData({...loginData, [e.target.name]: e.target.value});
    };

    const handleLoginSubmit = async (e) => {
      e.preventDefault();
      try {
        const res = await fetch(`${API_URL}/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(loginData)
        });
        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.message || "Login failed");
        }
        const data = await res.json();
        setAlert({ type: 'success', message: data.message });
        navigate("home");
      } catch (error) {
        setAlert({ type: 'error', message: error.message });
      }
    };

    return (
      <div>
        <h2>Login</h2>
        <form onSubmit={handleLoginSubmit}>
          <label>Username:
            <input type="text" name="username" value={loginData.username} onChange={handleLoginChange} required />
          </label>
          <label>Password:
            <input type="password" name="password" value={loginData.password} onChange={handleLoginChange} required />
          </label>
          <button type="submit">Login</button>
          <button type="button" onClick={() => navigate("home")}>Cancel</button>
        </form>
      </div>
    );
  };

  // Main Render based on current page state
  return (
    <div className="App">
      <header>
        <h1>Inventory Management</h1>
        <nav>
          <button onClick={() => navigate("home")}>Home</button>
          <button onClick={() => navigate("add")}>Add Item</button>
          <button onClick={() => navigate("login")}>Login</button>
        </nav>
      </header>
      {alert && <Alert type={alert.type} message={alert.message} />}
      <main>
        {page === "home" && <InventoryList />}
        {page === "add" && <ItemForm />}
        {page === "login" && <Login />}
      </main>
      <footer>
        <p>&copy; {new Date().getFullYear()} Inventory App</p>
      </footer>
    </div>
  );
};

// Mounting Logic: attach the App component to the DOM element with id "root"
const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);
root.render(<App />);
