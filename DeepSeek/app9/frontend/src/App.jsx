import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [items, setItems] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [formData, setFormData] = useState({ name: '', category: '', stock: '' });

  // Fetch items from the backend
  useEffect(() => {
    fetch('/api/items')
      .then((response) => response.json())
      .then((data) => setItems(data))
      .catch((error) => console.error('Error fetching items:', error));
  }, []);

  // Handle form input changes
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  // Add a new item
  const addItem = () => {
    fetch('/api/items', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    })
      .then((response) => response.json())
      .then((newItem) => {
        setItems([...items, newItem]);
        setFormData({ name: '', category: '', stock: '' });
      })
      .catch((error) => console.error('Error adding item:', error));
  };

  // Delete an item
  const deleteItem = (id) => {
    fetch(`/api/items/${id}`, { method: 'DELETE' })
      .then(() => setItems(items.filter((item) => item.id !== id)))
      .catch((error) => console.error('Error deleting item:', error));
  };

  // Filter items by search term
  const filteredItems = items.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="app">
      <h1>Inventory Management System</h1>
      <div className="form">
        <input
          type="text"
          name="name"
          placeholder="Item Name"
          value={formData.name}
          onChange={handleInputChange}
        />
        <input
          type="text"
          name="category"
          placeholder="Category"
          value={formData.category}
          onChange={handleInputChange}
        />
        <input
          type="number"
          name="stock"
          placeholder="Stock"
          value={formData.stock}
          onChange={handleInputChange}
        />
        <button onClick={addItem}>Add Item</button>
      </div>
      <input
        type="text"
        placeholder="Search Items"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <div className="items">
        {filteredItems.map((item) => (
          <div key={item.id} className="item">
            <h3>{item.name}</h3>
            <p>Category: {item.category}</p>
            <p>Stock: {item.stock}</p>
            <button onClick={() => deleteItem(item.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
