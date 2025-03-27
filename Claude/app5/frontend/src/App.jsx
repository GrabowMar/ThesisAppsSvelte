import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API service
const API_BASE_URL = 'http://localhost:5329/api';

const api = {
  async request(endpoint, options = {}) {
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    };
    
    const fetchOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'An error occurred');
      }
      
      return data;
    } catch (error) {
      console.error('API error:', error);
      throw error;
    }
  },
  
  // Auth methods
  login: (credentials) => api.request('/login', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (userData) => api.request('/register', { method: 'POST', body: JSON.stringify(userData) }),
  logout: () => api.request('/logout', { method: 'POST' }),
  checkAuth: () => api.request('/check-auth'),
  
  // Product methods
  getProducts: () => api.request('/products'),
  getProduct: (id) => api.request(`/products/${id}`),
  
  // Cart methods
  getCart: () => api.request('/cart'),
  addToCart: (item) => api.request('/cart', { method: 'POST', body: JSON.stringify(item) }),
  updateCartItem: (productId, quantity) => api.request(`/cart/${productId}`, { 
    method: 'PUT', 
    body: JSON.stringify({ quantity }) 
  }),
  removeFromCart: (productId) => api.request(`/cart/${productId}`, { method: 'DELETE' }),
  
  // Checkout methods
  checkout: (checkoutData) => api.request('/checkout', { method: 'POST', body: JSON.stringify(checkoutData) }),
  
  // Order methods
  getOrders: () => api.request('/orders'),
  getOrder: (id) => api.request(`/orders/${id}`),
};

// Context for Auth
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    checkAuthStatus();
  }, []);
  
  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const data = await api.checkAuth();
      setUser(data.authenticated ? data.user : null);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };
  
  const login = async (credentials) => {
    const data = await api.login(credentials);
    setUser(data.user);
    return data;
  };
  
  const register = async (userData) => {
    const data = await api.register(userData);
    setUser(data.user);
    return data;
  };
  
  const logout = async () => {
    await api.logout();
    setUser(null);
  };
  
  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Context for Cart
const CartContext = React.createContext(null);

function CartProvider({ children }) {
  const { isAuthenticated } = React.useContext(AuthContext);
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    } else {
      setCart({ items: [], total: 0 });
    }
  }, [isAuthenticated]);
  
  const fetchCart = async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    try {
      const cartData = await api.getCart();
      setCart(cartData);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const addToCart = async (productId, quantity) => {
    setLoading(true);
    try {
      await api.addToCart({ product_id: productId, quantity });
      await fetchCart();
      return true;
    } catch (error) {
      console.error('Error adding to cart:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const updateCartItem = async (productId, quantity) => {
    setLoading(true);
    try {
      await api.updateCartItem(productId, quantity);
      await fetchCart();
      return true;
    } catch (error) {
      console.error('Error updating cart:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const removeFromCart = async (productId) => {
    setLoading(true);
    try {
      await api.removeFromCart(productId);
      await fetchCart();
      return true;
    } catch (error) {
      console.error('Error removing from cart:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };
  
  const clearCart = () => {
    setCart({ items: [], total: 0 });
  };
  
  const value = {
    cart,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    refreshCart: fetchCart,
    clearCart,
  };
  
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

// Toast Component
function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 3000);
    
    return () => clearTimeout(timer);
  }, [onClose]);
  
  return (
    <div className={`toast toast-${type}`}>
      <p>{message}</p>
      <button onClick={onClose}>×</button>
    </div>
  );
}

function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast 
          key={toast.id} 
          message={toast.message} 
          type={toast.type} 
          onClose={() => removeToast(toast.id)} 
        />
      ))}
    </div>
  );
}

// Product card component
function ProductCard({ product, onAddToCart }) {
  const [quantity, setQuantity] = useState(1);
  
  const handleAddToCart = () => {
    onAddToCart(product.id, quantity);
    setQuantity(1);
  };
  
  return (
    <div className="product-card">
      <div className="product-image">
        <img src={`/images/${product.image}`} alt={product.name} onError={(e) => {
          e.target.onerror = null;
          e.target.src = 'https://via.placeholder.com/150';
        }} />
      </div>
      <div className="product-info">
        <h3>{product.name}</h3>
        <p className="product-price">${product.price.toFixed(2)}</p>
        <p className="product-description">{product.description}</p>
        <div className="stock-info">
          <span className={product.stock > 0 ? 'in-stock' : 'out-of-stock'}>
            {product.stock > 0 ? `In Stock (${product.stock})` : 'Out of Stock'}
          </span>
        </div>
      </div>
      <div className="product-actions">
        <div className="quantity-control">
          <button 
            onClick={() => setQuantity(q => Math.max(1, q - 1))}
            disabled={quantity <= 1}
          >-</button>
          <span>{quantity}</span>
          <button 
            onClick={() => setQuantity(q => Math.min(product.stock, q + 1))}
            disabled={quantity >= product.stock}
          >+</button>
        </div>
        <button 
          className="add-to-cart-btn" 
          onClick={handleAddToCart}
          disabled={product.stock <= 0}
        >
          {product.stock > 0 ? 'Add to Cart' : 'Out of Stock'}
        </button>
      </div>
    </div>
  );
}

// Cart Item component
function CartItem({ item, onUpdateQuantity, onRemove }) {
  return (
    <div className="cart-item">
      <div className="cart-item-image">
        <img src={`/images/${item.image}`} alt={item.name} onError={(e) => {
          e.target.onerror = null;
          e.target.src = 'https://via.placeholder.com/50';
        }} />
      </div>
      <div className="cart-item-details">
        <h4>{item.name}</h4>
        <p className="cart-item-price">${item.price.toFixed(2)}</p>
      </div>
      <div className="cart-item-actions">
        <div className="quantity-control">
          <button 
            onClick={() => onUpdateQuantity(item.product_id, item.quantity - 1)}
            disabled={item.quantity <= 1}
          >-</button>
          <span>{item.quantity}</span>
          <button onClick={() => onUpdateQuantity(item.product_id, item.quantity + 1)}>+</button>
        </div>
        <p className="cart-item-subtotal">${item.subtotal.toFixed(2)}</p>
        <button className="remove-btn" onClick={() => onRemove(item.product_id)}>×</button>
      </div>
    </div>
  );
}

// Pages
function HomePage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToCart } = React.useContext(CartContext);
  const { isAuthenticated } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  
  useEffect(() => {
    fetchProducts();
  }, []);
  
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await api.getProducts();
      setProducts(data);
    } catch (error) {
      addToast('Failed to load products', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddToCart = async (productId, quantity) => {
    if (!isAuthenticated) {
      addToast('Please log in to add items to your cart', 'warning');
      return;
    }
    
    try {
      const success = await addToCart(productId, quantity);
      if (success) {
        const product = products.find(p => p.id === productId);
        addToast(`Added ${product.name} to cart`, 'success');
      }
    } catch (error) {
      addToast(error.message || 'Failed to add item to cart', 'error');
    }
  };
  
  if (loading) {
    return <div className="loading">Loading products...</div>;
  }
  
  return (
    <div className="home-page">
      <h1>Our Products</h1>
      <div className="products-grid">
        {products.length > 0 ? (
          products.map((product) => (
            <ProductCard 
              key={product.id} 
              product={product} 
              onAddToCart={handleAddToCart} 
            />
          ))
        ) : (
          <p>No products available at the moment.</p>
        )}
      </div>
    </div>
  );
}

function CartPage() {
  const { cart, loading, updateCartItem, removeFromCart, refreshCart } = React.useContext(CartContext);
  const { isAuthenticated } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const navigate = useNavigate();
  
  useEffect(() => {
    if (isAuthenticated) {
      refreshCart();
    } else {
      navigate('/login');
    }
  }, [isAuthenticated, navigate, refreshCart]);
  
  const handleUpdateQuantity = async (productId, newQuantity) => {
    try {
      await updateCartItem(productId, newQuantity);
    } catch (error) {
      addToast(error.message || 'Failed to update cart', 'error');
    }
  };
  
  const handleRemoveItem = async (productId) => {
    try {
      await removeFromCart(productId);
      addToast('Item removed from cart', 'success');
    } catch (error) {
      addToast(error.message || 'Failed to remove item', 'error');
    }
  };
  
  if (loading) {
    return <div className="loading">Loading your cart...</div>;
  }
  
  return (
    <div className="cart-page">
      <h1>Your Shopping Cart</h1>
      
      {cart.items.length === 0 ? (
        <div className="empty-cart">
          <p>Your cart is empty</p>
          <button onClick={() => navigate('/')}>Continue Shopping</button>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {cart.items.map((item) => (
              <CartItem 
                key={item.product_id} 
                item={item} 
                onUpdateQuantity={handleUpdateQuantity}
                onRemove={handleRemoveItem} 
              />
            ))}
          </div>
          
          <div className="cart-summary">
            <h3>Cart Summary</h3>
            <div className="summary-row">
              <span>Subtotal:</span>
              <span>${cart.total.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>Shipping:</span>
              <span>Free</span>
            </div>
            <div className="summary-row total">
              <span>Total:</span>
              <span>${cart.total.toFixed(2)}</span>
            </div>
            <button 
              className="checkout-btn"
              onClick={() => navigate('/checkout')}
            >
              Proceed to Checkout
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function CheckoutPage() {
  const { cart, loading: cartLoading, clearCart } = React.useContext(CartContext);
  const { isAuthenticated, user } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    address: '',
    city: '',
    zip: '',
    
