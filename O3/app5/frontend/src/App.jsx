/*
E-Commerce Cart Application - Frontend (React)
This file contains the full frontend implementation including:
  - Multipage routing (using react-router-dom)
  - Product listing, cart management, checkout, orders summary
  - API calls with proper error handling and mounting logic
*/

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useNavigate
} from 'react-router-dom';
import './App.css';

const API_BASE = '/api'; // Will be proxied to backend (http://localhost:6149)

// Navbar Component for Navigation
function Navbar() {
  return (
    <nav className="navbar">
      <h1>E-Commerce Cart</h1>
      <ul className="nav-links">
        <li><Link to="/">Products</Link></li>
        <li><Link to="/cart">Cart</Link></li>
        <li><Link to="/orders">Orders</Link></li>
      </ul>
    </nav>
  );
}

// Home Page: Displays product listing
function Products() {
  const [products, setProducts] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/products`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setProducts(data.products);
        } else {
          setError(data.message || "Failed to load products.");
        }
      })
      .catch(() => setError("Error connecting to server."));
  }, []);

  // Add selected product to cart using the provided quantity.
  const addToCart = (productId, quantity) => {
    if (quantity <= 0) {
      alert("Quantity must be greater than zero");
      return;
    }
    fetch(`${API_BASE}/cart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("Product added to cart!");
        } else {
          alert(data.message || "Failed to add to cart.");
        }
      })
      .catch(() => alert("Error adding to cart."));
  };

  return (
    <div className="container">
      <h2>Products</h2>
      {error && <div className="error">{error}</div>}
      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <h3>{product.name}</h3>
            <p>{product.description}</p>
            <p>Price: ${product.price.toFixed(2)}</p>
            <p>In Stock: {product.inventory}</p>
            <div>
              <input id={`qty-${product.id}`} type="number" defaultValue={1} min={1} />
              <button onClick={() => {
                const qty = parseInt(document.getElementById(`qty-${product.id}`).value);
                addToCart(product.id, qty);
              }}>Add to Cart</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Cart Page: Displays current cart items, allows removal and checkout.
function Cart() {
  const [cart, setCart] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchCart = () => {
    fetch(`${API_BASE}/cart`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setCart(data.cart);
        } else {
          setError(data.message || "Failed to load cart.");
        }
      })
      .catch(() => setError("Error connecting to server."));
  };

  useEffect(() => {
    fetchCart();
  }, []);

  const removeFromCart = (productId) => {
    fetch(`${API_BASE}/cart/${productId}`, {
      method: 'DELETE'
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          fetchCart();
        } else {
          alert(data.message || "Failed to remove item.");
        }
      })
      .catch(() => alert("Error removing item from cart."));
  };

  const handleCheckout = () => {
    fetch(`${API_BASE}/checkout`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("Checkout successful!");
          navigate('/orders');
        } else {
          alert(data.message || "Checkout failed.");
        }
        fetchCart();
      })
      .catch(() => alert("Error during checkout."));
  };

  const cartTotal = cart.reduce((total, item) => total + item.price * item.quantity, 0);

  return (
    <div className="container">
      <h2>Your Cart</h2>
      {error && <div className="error">{error}</div>}
      {cart.length === 0 ? (
        <p>Your cart is empty.</p>
      ) : (
        <div>
          <table className="cart-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Price</th>
                <th>Quantity</th>
                <th>Subtotal</th>
                <th>Remove</th>
              </tr>
            </thead>
            <tbody>
              {cart.map(item => (
                <tr key={item.id}>
                  <td>{item.name}</td>
                  <td>${item.price.toFixed(2)}</td>
                  <td>{item.quantity}</td>
                  <td>${(item.price * item.quantity).toFixed(2)}</td>
                  <td>
                    <button onClick={() => removeFromCart(item.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="cart-summary">
            <h3>Total: ${cartTotal.toFixed(2)}</h3>
            <button onClick={handleCheckout}>Proceed to Checkout</button>
          </div>
        </div>
      )}
    </div>
  );
}

// Orders Page: Displays list of finalized orders.
function Orders() {
  const [orders, setOrders] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/orders`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setOrders(data.orders);
        } else {
          setError(data.message || "Failed to load orders.");
        }
      })
      .catch(() => setError("Error connecting to server."));
  }, []);

  return (
    <div className="container">
      <h2>Your Orders</h2>
      {error && <div className="error">{error}</div>}
      {orders.length === 0 ? (
        <p>No orders found.</p>
      ) : (
        orders.map(order => (
          <div key={order.order_id} className="order-card">
            <h3>Order #{order.order_id}</h3>
            <ul>
              {order.items.map(item => (
                <li key={item.id}>
                  {item.name} - Qty: {item.quantity} - ${item.price.toFixed(2)} each
                </li>
              ))}
            </ul>
            <h4>Total: ${order.total.toFixed(2)}</h4>
          </div>
        ))
      )}
    </div>
  );
}

// Main App Component with Routing
function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Products />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="*" element={<div className="container"><h2>Page not found</h2></div>} />
      </Routes>
    </Router>
  );
}

// Mounting the React application to the DOM element with id "root"
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
