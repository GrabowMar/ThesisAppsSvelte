import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);

  useEffect(() => {
    fetch('/api/products')
      .then(response => response.json())
      .then(data => setProducts(data));

    fetch('/api/cart')
      .then(response => response.json())
      .then(data => setCart(data));
  }, []);

  const addToCart = (productId, quantity) => {
    fetch('/api/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity })
    })
      .then(response => response.json())
      .then(data => {
        if (response.ok) {
          setCart(prevCart => [...prevCart, { product_id: productId, quantity }]);
        } else {
          alert(data.message);
        }
      });
  };

  const checkout = () => {
    fetch('/api/checkout', { method: 'POST' })
      .then(response => response.json())
      .then(data => {
        setCart([]);
        alert('Order placed successfully!');
      });
  };

  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li><Link to="/">Products</Link></li>
            <li><Link to="/cart">Cart</Link></li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={
            <div>
              <h1>Products</h1>
              <ul>
                {products.map(product => (
                  <li key={product.id}>
                    {product.name} - ${product.price.toFixed(2)}
                    <button onClick={() => addToCart(product.id, 1)}>Add to Cart</button>
                  </li>
                ))}
              </ul>
            </div>
          } />
          <Route path="/cart" element={
            <div>
              <h1>Cart</h1>
              <ul>
                {cart.map(item => (
                  <li key={item.product_id}>
                    Product ID: {item.product_id} - Quantity: {item.quantity}
                  </li>
                ))}
              </ul>
              <button onClick={checkout}>Checkout</button>
            </div>
          } />
        </Routes>
      </div>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
