import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  // 1. State Management
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({});  // {productId: quantity}
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePage, setActivePage] = useState('products'); // products, cart, checkout
  const [checkoutMessage, setCheckoutMessage] = useState('');


  // 2. Lifecycle Functions
  useEffect(() => {
    fetchProducts();
  }, []);

  // 3. API Calls
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/products');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setProducts(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const updateCartItem = async (productId, quantity, action) => {
    try {
      const response = await fetch('/api/cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ productId, quantity, action }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      fetchProducts()  //re-fetch to update quantity
      return data

    } catch (error) {
      console.error("Error updating cart:", error);
      setError(error.message)
    }
  };


  const handleAddToCart = async (productId) => {
    const response = await updateCartItem(productId, 1, "add")
    if (response) {
      const newCart = { ...cart };
      newCart[productId] = (newCart[productId] || 0) + 1;
      setCart(newCart);
    }

  };

  const handleRemoveFromCart = async (productId) => {
    if (!cart[productId]) return;
    const response = await updateCartItem(productId, 1, "remove")
    if (response) {
      const newCart = { ...cart };
      newCart[productId] -= 1;
      if (newCart[productId] === 0) {
        delete newCart[productId];
      }
      setCart(newCart);
    }
  };


  const handleCheckout = async () => {
    // Prepare the cart items for the checkout API
    const cartItems = Object.keys(cart).map(productId => ({
        productId: parseInt(productId),
        quantity: cart[productId]
    }));

    try {
        const response = await fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cartItems: cartItems })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setCheckoutMessage(data.message);
        setCart({});  // Clear the cart on successful checkout
        setActivePage('orderSummary'); // Navigate to order summary page
    } catch (error) {
        console.error("Checkout error:", error);
        setError(error.message);
    }
  };



  // 4. Render Functions/UI Components

  const renderProducts = () => {
    return (
      <div>
        <h2>Products</h2>
        {loading && <p>Loading products...</p>}
        {error && <p>Error: {error}</p>}
        <div className="products-grid">
          {products.map((product) => (
            <div key={product.id} className="product-card">
              <img src={product.image} alt={product.name} />
              <h3>{product.name}</h3>
              <p>Price: ${product.price}</p>
              <p>Inventory: {product.inventory}</p>
              <button onClick={() => handleAddToCart(product.id)} disabled={product.inventory === 0}>
                Add to Cart
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderCart = () => {
    const cartItems = Object.keys(cart).map((productId) => {
      const product = products.find((p) => p.id === parseInt(productId));
      return {
        ...product,
        quantity: cart[productId],
      };
    });

    return (
      <div>
        <h2>Cart</h2>
        {cartItems.length === 0 ? (
          <p>Your cart is empty.</p>
        ) : (
          <>
            <ul className="cart-items">
              {cartItems.map((item) => (
                <li key={item.id}>
                  {item.name} - Quantity: {item.quantity}
                  <button onClick={() => handleRemoveFromCart(item.id)}>Remove</button>
                </li>
              ))}
            </ul>
            <button onClick={handleCheckout}>Checkout</button>
          </>
        )}
      </div>
    );
  };

  const renderOrderSummary = () => {
    return (
        <div>
            <h2>Order Summary</h2>
            <p>{checkoutMessage || "Your order was successfully placed!"}</p>
            <button onClick={() => setActivePage('products')}>Back to Products</button>
        </div>
    );
  };



  // 5. Main Render
  return (
    <div className="app-container">
      <header>
        <h1>E-Commerce Store</h1>
        <nav>
          <button onClick={() => setActivePage('products')}>Products</button>
          <button onClick={() => setActivePage('cart')}>Cart ({Object.keys(cart).length})</button>
          {checkoutMessage && <button onClick={() => setActivePage('orderSummary')}>Order Summary</button>}

        </nav>
      </header>
      <main>
        {activePage === 'products' && renderProducts()}
        {activePage === 'cart' && renderCart()}
        {activePage === 'orderSummary' && renderOrderSummary()}
      </main>
      <footer>
        <p>&copy; 2024 E-Commerce Store</p>
      </footer>
    </div>
  );
}

// 6. Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
