import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './App.css';

const App = () => {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ name: '', category: '', stock: '', alert_level: '' });

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    const response = await axios.get('/api/items');
    setItems(response.data);
  };

  const createItem = async () => {
    const response = await axios.post('/api/items', form);
    setItems([...items, response.data]);
    setForm({ name: '', category: '', stock: '', alert_level: '' });
  };

  const updateItem = async (id) => {
    const response = await axios.put(`/api/items/${id}`, form);
    setItems(items.map(item => item.id === id ? response.data : item));
  };

  const deleteItem = async (id) => {
    await axios.delete(`/api/items/${id}`);
    setItems(items.filter(item => item.id !== id));
  };

  return (
    <div className="app">
      <h1>Inventory Management</h1>
      <div className="form">
        <input type="text" placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input type="text" placeholder="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
        <input type="number" placeholder="Stock" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} />
        <input type="number" placeholder="Alert Level" value={form.alert_level} onChange={(e) => setForm({ ...form, alert_level: e.target.value })} />
        <button onClick={createItem}>Add Item</button>
      </div>
      <div className="items">
        {items.map(item => (
          <div key={item.id} className="item">
            <h2>{item.name}</h2>
            <p>Category: {item.category}</p>
            <p>Stock: {item.stock}</p>
            <p>Alert Level: {item.alert_level}</p>
            <button onClick={() => updateItem(item.id)}>Update</button>
            <button onClick={() => deleteItem(item.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
