import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:XXXX/items';

const ItemList = () => {
  const [items, setItems] = useState([]);

  useEffect(() => {
    axios.get(API_URL).then(response => setItems(response.data));
  }, []);

  return (
    <div>
      <h1>Item List</h1>
      <ul>
        {items.map(item => (
          <li key={item.id}>{item.name} - {item.category} - Stock: {item.stock}</li>
        ))}
      </ul>
    </div>
  );
};

const ItemForm = () => {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [stock, setStock] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    axios.post(API_URL, { name, category, stock }).then(() => {
      setName('');
      setCategory('');
      setStock('');
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <h1>Add Item</h1>
      <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" required />
      <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="Category" required />
      <input type="number" value={stock} onChange={(e) => setStock(e.target.value)} placeholder="Stock" required />
      <button type="submit">Add Item</button>
    </form>
  );
};

const App = () => {
  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/add">Add Item</Link>
      </nav>
      <Routes>
        <Route path="/" element={<ItemList />} />
        <Route path="/add" element={<ItemForm />} />
      </Routes>
    </Router>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
