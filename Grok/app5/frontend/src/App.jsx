import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentPage, setCurrentPage] = useState('home');

  // Fetch products
  useEffect(() => {
    fetch('http://localhost:5989/api/products')
      .then(response => response.json())
      .then(data => setProducts(data))
      .catch(error => console.error('Error fetching products:', error));
  }, []);

  // Login function
  const login = async (username, password) => {
    try {
      const response = await fetch('http://localhost:5989/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setIsAuthenticated(true);
        localStorage.setItem('token', data.token);
      } else {
        alert(data.error);
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  // Add to cart
  const addToCart = async (productId, quantity) => {
    try {
      const response = await fetch('http://localhost:5989/api/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-User': 'currentUser', // In a real app, this would be the actual user
        },
        body: JSON.stringify({ productId, quantity }),
      });
      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        fetchCart();
      } else {
        alert(data.error);
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
    }
  };

  // Fetch cart
  const fetchCart = async () => {
    try {
      const response = await fetch('http://localhost:5989/api/cart', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-User': 'currentUser',
        },
      });
      const data = await response.json();
      setCart(data);
    } catch (error) {
      console.error('Error fetching cart:', error);
    }
  };

  // Checkout
  const checkout = async () => {
    try {
      const response = await fetch('http://localhost:5989/api/checkout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-User': 'currentUser',
        },
      });
      const data = await response.json();
      if (response.ok) {
        alert(`Order placed successfully! Total: $${data.total}`);
        setCart([]);
      } else {
        alert(data.error);
      }
    } catch (error) {
      console.error('Checkout error:', error);
    }
  };

  // Render different pages
  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return (
          <div>
            <h1>Welcome to the E-commerce Store</h1>
            <button onClick={() => setCurrentPage('products')}>View Products</button>
            <button onClick={() => setCurrentPage('cart')}>View Cart</button>
            {!isAuthenticated && <button onClick={() => setCurrentPage('login')}>Login</button>}
          </div>
        );
      case 'products':
        return (
          <div>
            <h1>Products</h1>
            <ul>
              {products.map(product => (
                <li key={product.id}>
                  {product.name} - ${product.price}
                  <button onClick={() => addToCart(product.id, 1)}>Add to Cart</button>
                </li>
              ))}
            </ul>
            <button onClick={() => setCurrentPage('home')}>Back to Home</button>
          </div>
        );
      case 'cart':
        return (
          <div>
            <h1>Shopping Cart</h1>
            <ul>
              {cart.map(item => (
                <li key={item.productId}>
                  {item.name} - ${item.price} x {item.quantity}
                </li>
              ))}
            </ul>
            {cart.length > 0 && <button onClick={checkout}>Checkout</button>}
            <button onClick={() => setCurrentPage('home')}>Back to Home</button>
          </div>
        );
      case 'login':
        return (
          <div>
            <h1>Login</h1>
            <input type="text" placeholder="Username" id="username" />
            <input type="password" placeholder="Password" id="password" />
            <button onClick={() => login(document.getElementById('username').value, document.getElementById('password').value)}>Login</button>
            <button onClick={() => setCurrentPage('home')}>Back to Home</button>
          </div>
        );
      default:
        return <div>Page not found</div>;
    }
  };

  return (
    <div className="App">
      {renderPage()}
    </div>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
