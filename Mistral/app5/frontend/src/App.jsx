import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5089/products')
      .then(response => setProducts(response.data))
      .catch(error => console.error('Error fetching products:', error));

    axios.get('http://localhost:5089/cart')
      .then(response => setCart(response.data))
      .catch(error => console.error('Error fetching cart:', error));

    axios.get('http://localhost:5089/orders')
      .then(response => setOrders(response.data))
      .catch(error => console.error('Error fetching orders:', error));
  }, []);

  const addToCart = (productId, quantity) => {
    axios.post('http://localhost:5089/cart', { product_id: productId, quantity })
      .then(response => {
        alert(response.data.message);
        axios.get('http://localhost:5089/cart')
          .then(response => setCart(response.data))
          .catch(error => console.error('Error fetching cart:', error));
      })
      .catch(error => alert('Error adding to cart: ' + error.response.data.message));
  };

  const checkout = () => {
    axios.post('http://localhost:5089/checkout')
      .then(response => {
        alert('Checkout successful!');
        setCart([]);
        setOrders([...orders, response.data]);
      })
      .catch(error => alert('Error during checkout: ' + error.response.data.message));
  };

  return (
    <Router>
      <nav>
        <Link to="/">Products</Link>
        <Link to="/cart">Cart</Link>
        <Link to="/orders">Orders</Link>
      </nav>
      <Routes>
        <Route path="/" element={
          <div>
            <h1>Products</h1>
            <ul>
              {products.map(product => (
                <li key={product.id}>
                  {product.name} - ${product.price} - Quantity: {product.quantity}
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
              {cart.map((item, index) => (
                <li key={index}>
                  Product ID: {item.product_id} - Quantity: {item.quantity}
                </li>
              ))}
            </ul>
            <button onClick={checkout}>Checkout</button>
          </div>
        } />
        <Route path="/orders" element={
          <div>
            <h1>Orders</h1>
            <ul>
              {orders.map((order, index) => (
                <li key={index}>
                  Order Total: ${order.total}
                  <ul>
                    {order.products.map((item, idx) => (
                      <li key={idx}>Product ID: {item.product_id} - Quantity: {item.quantity}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </div>
        } />
      </Routes>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
