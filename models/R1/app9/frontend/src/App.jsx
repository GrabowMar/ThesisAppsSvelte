import { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// Main Inventory Component
function InventoryList() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [editItem, setEditItem] = useState(null);

  // Fetch items with filters
  const fetchItems = async() => {
    const params = new URLSearchParams({
      q: search,
      category: category === 'all' ? '' : category
    });
    
    try {
      const response = await fetch(`/api/items?${params}`);
      const data = await response.json();
      setItems(data);
    } catch (error) {
      console.error('Error fetching items:', error);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [search, category]);

  // Get unique categories
  const categories = ['all', ...new Set(items.map(item => item.category))];

  return (
    <div className="container">
      <div className="controls">
        <input
          type="text"
          placeholder="Search items..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <button onClick={() => setShowCreate(true)}>Add Item</button>
        <Link to="/low-stock" className="nav-link">Low Stock Alerts</Link>
      </div>

      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Category</th>
            <th>Stock</th>
            <th>Min Stock</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id} className={item.stock < item.min_stock ? 'low-stock' : ''}>
              <td>{item.name}</td>
              <td>{item.category}</td>
              <td>{item.stock}</td>
              <td>{item.min_stock}</td>
              <td>
                <button onClick={() => setEditItem(item)}>Edit</button>
                <button onClick={async() => {
                  await fetch(`/api/items/${item.id}`, { method: 'DELETE' });
                  fetchItems();
                }}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Create/Edit Modals */}
      {(showCreate || editItem) && <ItemModal 
        item={editItem}
        onClose={() => { setShowCreate(false); setEditItem(null); }}
        onSave={fetchItems}
      />}
    </div>
  );
}

// Low Stock Component
function LowStock() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const fetchLowStock = async() => {
      try {
        const response = await fetch('/api/items/low-stock');
        const data = await response.json();
        setItems(data);
      } catch (error) {
        console.error('Error fetching low stock:', error);
      }
    };
    fetchLowStock();
  }, []);

  return (
    <div className="container">
      <Link to="/" className="nav-link">Back to Inventory</Link>
      <h2>Low Stock Alerts</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Current Stock</th>
            <th>Minimum Required</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id} className="low-stock">
              <td>{item.name}</td>
              <td>{item.stock}</td>
              <td>{item.min_stock}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Modal Component
function ItemModal({ item, onClose, onSave }) {
  const [form, setForm] = useState(item || {
    name: '',
    category: '',
    stock: 0,
    min_stock: 0
  });

  const handleSubmit = async(e) => {
    e.preventDefault();
    const url = item ? `/api/items/${item.id}` : '/api/items';
    const method = item ? 'PUT' : 'POST';
    
    try {
      await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      onSave();
      onClose();
    } catch (error) {
      console.error('Error saving item:', error);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h2>{item ? 'Edit Item' : 'New Item'}</h2>
        <form onSubmit={handleSubmit}>
          <label>
            Name:
            <input 
              required
              value={form.name}
              onChange={e => setForm({...form, name: e.target.value})}
            />
          </label>
          <label>
            Category:
            <input 
              value={form.category}
              onChange={e => setForm({...form, category: e.target.value})}
            />
          </label>
          <label>
            Stock:
            <input
              type="number"
              value={form.stock}
              onChange={e => setForm({...form, stock: parseInt(e.target.value) || 0})}
            />
          </label>
          <label>
            Min Stock:
            <input
              type="number"
              value={form.min_stock}
              onChange={e => setForm({...form, min_stock: parseInt(e.target.value) || 0})}
            />
          </label>
          <div className="modal-actions">
            <button type="button" onClick={onClose}>Cancel</button>
            <button type="submit">Save</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<InventoryList />} />
        <Route path="/low-stock" element={<LowStock />} />
      </Routes>
    </Router>
  );
}

// Mount React
const root = createRoot(document.getElementById('root'));
root.render(<App />);
