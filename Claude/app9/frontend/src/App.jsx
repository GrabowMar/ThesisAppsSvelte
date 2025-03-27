// App.jsx - Frontend for Inventory Management System
import React, { useState, useEffect, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import './App.css';

// API Service
const API_URL = 'http://localhost:5337/api';

const apiService = {
  // Items
  getItems: async (filters = {}) => {
    const queryParams = new URLSearchParams();
    if (filters.category_id) queryParams.append('category_id', filters.category_id);
    if (filters.search) queryParams.append('search', filters.search);
    if (filters.low_stock) queryParams.append('low_stock', filters.low_stock);
    
    const response = await fetch(`${API_URL}/items?${queryParams}`);
    if (!response.ok) throw new Error('Failed to fetch items');
    return response.json();
  },
  
  getItem: async (id) => {
    const response = await fetch(`${API_URL}/items/${id}`);
    if (!response.ok) throw new Error('Failed to fetch item');
    return response.json();
  },
  
  createItem: async (item) => {
    const response = await fetch(`${API_URL}/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create item');
    }
    return response.json();
  },
  
  updateItem: async (id, item) => {
    const response = await fetch(`${API_URL}/items/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(item)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update item');
    }
    return response.json();
  },
  
  deleteItem: async (id) => {
    const response = await fetch(`${API_URL}/items/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete item');
    }
    return response.json();
  },
  
  // Categories
  getCategories: async () => {
    const response = await fetch(`${API_URL}/categories`);
    if (!response.ok) throw new Error('Failed to fetch categories');
    return response.json();
  },
  
  createCategory: async (category) => {
    const response = await fetch(`${API_URL}/categories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(category)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create category');
    }
    return response.json();
  },
  
  updateCategory: async (id, category) => {
    const response = await fetch(`${API_URL}/categories/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(category)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to update category');
    }
    return response.json();
  },
  
  deleteCategory: async (id) => {
    const response = await fetch(`${API_URL}/categories/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to delete category');
    }
    return response.json();
  },
  
  // Dashboard
  getDashboard: async () => {
    const response = await fetch(`${API_URL}/dashboard`);
    if (!response.ok) throw new Error('Failed to fetch dashboard data');
    return response.json();
  }
};

function App() {
  // State initialization
  const [page, setPage] = useState('dashboard');
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [dashboardData, setDashboardData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    category_id: '',
    search: '',
    low_stock: false
  });
  
  // Form states
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalType, setModalType] = useState('');
  const [formData, setFormData] = useState({});
  const [formErrors, setFormErrors] = useState({});
  
  // Fetch items based on current filters
  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getItems(filters);
      setItems(data);
      setError(null);
    } catch (err) {
      setError('Failed to load items. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [filters]);
  
  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getCategories();
      setCategories(data);
      setError(null);
    } catch (err) {
      setError('Failed to load categories. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Fetch dashboard data
  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getDashboard();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Handle filter changes
  const handleFilterChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  // Modal and form handlers
  const openModal = (type, item = null, category = null) => {
    setModalType(type);
    
    if (type === 'addItem' || type === 'editItem') {
      setSelectedItem(item);
      setFormData(item || { 
        name: '', 
        description: '', 
        quantity: 0, 
        price: 0, 
        reorder_level: 5,
        category_id: ''
      });
    } else if (type === 'addCategory' || type === 'editCategory') {
      setSelectedCategory(category);
      setFormData(category || { name: '', description: '' });
    } else if (type === 'deleteItem') {
      setSelectedItem(item);
    } else if (type === 'deleteCategory') {
      setSelectedCategory(category);
    }
    
    setFormErrors({});
    setIsModalOpen(true);
  };
  
  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedItem(null);
    setSelectedCategory(null);
    setFormData({});
    setFormErrors({});
  };
  
  const handleFormChange = (e) => {
    const { name, value, type } = e.target;
    let processedValue = value;
    
    // Handle numeric inputs
    if (type === 'number') {
      processedValue = value === '' ? '' : Number(value);
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }));
    
    // Clear error for the changed field
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };
  
  const validateItemForm = () => {
    const errors = {};
    
    if (!formData.name?.trim()) {
      errors.name = 'Name is required';
    }
    
    if (formData.quantity === '') {
      errors.quantity = 'Quantity is required';
    } else if (formData.quantity < 0) {
      errors.quantity = 'Quantity cannot be negative';
    }
    
    if (formData.price === '') {
      errors.price = 'Price is required';
    } else if (formData.price < 0) {
      errors.price = 'Price cannot be negative';
    }
    
    if (formData.reorder_level === '') {
      errors.reorder_level = 'Reorder level is required';
    } else if (formData.reorder_level < 0) {
      errors.reorder_level = 'Reorder level cannot be negative';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  const validateCategoryForm = () => {
    const errors = {};
    
    if (!formData.name?.trim()) {
      errors.name = 'Name is required';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Form submission handlers
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (modalType === 'addItem') {
        if (!validateItemForm()) return;
        await apiService.createItem(formData);
        await fetchItems();
        await fetchDashboard();
      } else if (modalType === 'editItem') {
        if (!validateItemForm()) return;
        await apiService.updateItem(selectedItem.id, formData);
        await fetchItems();
        await fetchDashboard();
      } else if (modalType === 'addCategory') {
        if (!validateCategoryForm()) return;
        await apiService.createCategory(formData);
        await fetchCategories();
        await fetchDashboard();
      } else if (modalType === 'editCategory') {
        if (!validateCategoryForm()) return;
        await apiService.updateCategory(selectedCategory.id, formData);
        await fetchCategories();
        await fetchItems();
        await fetchDashboard();
      } else if (modalType === 'deleteItem') {
        await apiService.deleteItem(selectedItem.id);
        await fetchItems();
        await fetchDashboard();
      } else if (modalType === 'deleteCategory') {
        await apiService.deleteCategory(selectedCategory.id);
        await fetchCategories();
        await fetchItems();
        await fetchDashboard();
      }
      
      setError(null);
      closeModal();
    } catch (err) {
      setError(err.message || 'An error occurred during the operation.');
      console.error(err);
    }
  };
  
  // Navigation handler
  const navigateTo = (pageName) => {
    setPage(pageName);
    setError(null);
  };
  
  // Effect for loading initial data
  useEffect(() => {
    if (page === 'dashboard') {
      fetchDashboard();
    } else if (page === 'inventory') {
      fetchItems();
      fetchCategories();
    } else if (page === 'categories') {
      fetchCategories();
    }
  }, [page, fetchItems, fetchCategories, fetchDashboard]);
  
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>Inventory Management System</h1>
        <div className="nav-container">
          <nav className="main-nav">
            <button 
              className={page === 'dashboard' ? 'active' : ''} 
              onClick={() => navigateTo('dashboard')}
            >
              Dashboard
            </button>
            <button 
              className={page === 'inventory' ? 'active' : ''} 
              onClick={() => navigateTo('inventory')}
            >
              Inventory
            </button>
            <button 
              className={page === 'categories' ? 'active' : ''} 
              onClick={() => navigateTo('categories')}
            >
              Categories
            </button>
          </nav>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="main-content">
        {/* Error notification */}
        {error && <div className="error-message">{error}</div>}
        
        {/* Loading indicator */}
        {loading && <div className="loading-spinner">Loading...</div>}
        
        {/* Dashboard Page */}
        {page === 'dashboard' && !loading && (
          <div className="dashboard">
            <h2>Dashboard</h2>
            
            <div className="dashboard-cards">
              <div className="dashboard-card">
                <h3>Total Items</h3>
                <p className="dashboard-value">{dashboardData.total_items || 0}</p>
              </div>
              
              <div className="dashboard-card">
                <h3>Total Categories</h3>
                <p className="dashboard-value">{dashboardData.total_categories || 0}</p>
              </div>
              
              <div className="dashboard-card">
                <h3>Total Quantity</h3>
                <p className="dashboard-value">{dashboardData.total_quantity || 0}</p>
              </div>
              
              <div className="dashboard-card low-stock">
                <h3>Low Stock Items</h3>
                <p className="dashboard-value">{dashboardData.low_stock_count || 0}</p>
              </div>
            </div>
            
            <div className="dashboard-sections">
              <div className="dashboard-section">
                <h3>Top Items by Value</h3>
                {dashboardData.top_items?.length > 0 ? (
                  <table className="dashboard-table">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th>Total Value</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.top_items.map(item => (
                        <tr key={item.id}>
                          <td>{item.name}</td>
                          <td>${item.value.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p>No items found</p>
                )}
              </div>
              
              <div className="dashboard-section">
                <h3>Categories Overview</h3>
                {dashboardData.category_stats?.length > 0 ? (
                  <table className="dashboard-table">
                    <thead>
                      <tr>
                        <th>Category</th>
                        <th>Item Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardData.category_stats.map(cat => (
                        <tr key={cat.id}>
                          <td>{cat.name}</td>
                          <td>{cat.item_count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p>No categories found</p>
                )}
              </div>
            </div>
            
            <div className="dashboard-actions">
              <button onClick={() => navigateTo('inventory')} className="btn primary">
                Manage Inventory
              </button>
              <button onClick={() => navigateTo('categories')} className="
