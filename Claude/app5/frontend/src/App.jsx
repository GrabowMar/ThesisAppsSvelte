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
    payment_method: 'credit_card'
  });
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (user) {
      setFormData(prev => ({
        ...prev,
        name: user.username || '',
        email: user.email || '',
      }));
    }
  }, [isAuthenticated, navigate, user]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (cart.items.length === 0) {
      addToast('Your cart is empty', 'warning');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.checkout(formData);
      clearCart();
      addToast('Order placed successfully!', 'success');
      navigate(`/order-confirmation/${response.order.id}`);
    } catch (error) {
      addToast(error.message || 'Failed to process checkout', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  if (cartLoading) {
    return <div className="loading">Loading checkout information...</div>;
  }
  
  return (
    <div className="checkout-page">
      <h1>Checkout</h1>
      
      <div className="checkout-container">
        <div className="checkout-form-container">
          <h2>Shipping Information</h2>
          <form onSubmit={handleSubmit} className="checkout-form">
            <div className="form-group">
              <label htmlFor="name">Full Name</label>
              <input 
                type="text" 
                id="name" 
                name="name" 
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input 
                type="email" 
                id="email" 
                name="email" 
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="address">Address</label>
              <input 
                type="text" 
                id="address" 
                name="address" 
                value={formData.address}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="city">City</label>
                <input 
                  type="text" 
                  id="city" 
                  name="city" 
                  value={formData.city}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="zip">ZIP Code</label>
                <input 
                  type="text" 
                  id="zip" 
                  name="zip" 
                  value={formData.zip}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>
            
            <h2>Payment Method</h2>
            <div className="payment-methods">
              <div className="payment-method">
                <input 
                  type="radio" 
                  id="credit_card" 
                  name="payment_method" 
                  value="credit_card"
                  checked={formData.payment_method === 'credit_card'}
                  onChange={handleChange}
                />
                <label htmlFor="credit_card">Credit Card</label>
              </div>
              
              <div className="payment-method">
                <input 
                  type="radio" 
                  id="paypal" 
                  name="payment_method" 
                  value="paypal"
                  checked={formData.payment_method === 'paypal'}
                  onChange={handleChange}
                />
                <label htmlFor="paypal">PayPal</label>
              </div>
            </div>
            
            <button 
              type="submit" 
              className="place-order-btn"
              disabled={loading || cart.items.length === 0}
            >
              {loading ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        </div>
        
        <div className="order-summary">
          <h2>Order Summary</h2>
          <div className="order-items">
            {cart.items.map((item) => (
              <div key={item.product_id} className="order-item">
                <span className="item-name">{item.name} × {item.quantity}</span>
                <span className="item-price">${item.subtotal.toFixed(2)}</span>
              </div>
            ))}
          </div>
          
          <div className="order-total">
            <span>Total</span>
            <span>${cart.total.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function OrderConfirmationPage() {
  const { addToast } = React.useContext(ToastContext);
  const { isAuthenticated } = React.useContext(AuthContext);
  const navigate = useNavigate();
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    fetchOrder();
  }, [isAuthenticated, navigate, orderId]);
  
  const fetchOrder = async () => {
    setLoading(true);
    try {
      const data = await api.getOrder(orderId);
      setOrder(data);
    } catch (error) {
      addToast('Failed to load order details', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div className="loading">Loading order details...</div>;
  }
  
  if (!order) {
    return (
      <div className="order-not-found">
        <h1>Order Not Found</h1>
        <p>We couldn't find the order you're looking for.</p>
        <button onClick={() => navigate('/orders')}>View All Orders</button>
      </div>
    );
  }
  
  return (
    <div className="order-confirmation">
      <div className="success-message">
        <h1>Order Confirmed!</h1>
        <p>Thank you for your purchase. Your order has been placed successfully.</p>
        <p className="order-number">Order #: {order.id}</p>
      </div>
      
      <div className="order-details">
        <h2>Order Details</h2>
        <div className="order-info">
          <div className="order-info-row">
            <span>Order Date:</span>
            <span>{new Date(order.created_at).toLocaleDateString()}</span>
          </div>
          <div className="order-info-row">
            <span>Order Status:</span>
            <span className={`status-${order.status}`}>{order.status}</span>
          </div>
          <div className="order-info-row">
            <span>Payment Method:</span>
            <span>{order.payment_method}</span>
          </div>
        </div>
        
        <h3>Shipping Address</h3>
        <div className="shipping-address">
          <p>{order.shipping_address.address}</p>
          <p>{order.shipping_address.city}, {order.shipping_address.zip}</p>
        </div>
        
        <h3>Order Summary</h3>
        <div className="order-items">
          {order.items.map((item, index) => (
            <div key={index} className="order-item">
              <div className="item-info">
                <span className="item-name">{item.name}</span>
                <span className="item-quantity">Qty: {item.quantity}</span>
              </div>
              <div className="item-price">${item.subtotal.toFixed(2)}</div>
            </div>
          ))}
        </div>
        
        <div className="order-total">
          <span>Total</span>
          <span>${order.total.toFixed(2)}</span>
        </div>
      </div>
      
      <div className="order-actions">
        <button onClick={() => navigate('/')}>Continue Shopping</button>
        <button onClick={() => navigate('/orders')}>View All Orders</button>
      </div>
    </div>
  );
}

function OrdersPage() {
  const { isAuthenticated } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    fetchOrders();
  }, [isAuthenticated, navigate]);
  
  const fetchOrders = async () => {
    setLoading(true);
    try {
      const data = await api.getOrders();
      setOrders(data);
    } catch (error) {
      addToast('Failed to load orders', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div className="loading">Loading orders...</div>;
  }
  
  return (
    <div className="orders-page">
      <h1>Your Orders</h1>
      
      {orders.length === 0 ? (
        <div className="empty-orders">
          <p>You haven't placed any orders yet.</p>
          <button onClick={() => navigate('/')}>Start Shopping</button>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order) => (
            <div key={order.id} className="order-card">
              <div className="order-header">
                <div className="order-header-left">
                  <h3>Order #{order.id.slice(0, 8)}</h3>
                  <p className="order-date">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`order-status status-${order.status}`}>
                  {order.status}
                </span>
              </div>
              
              <div className="order-items-preview">
                {order.items.slice(0, 2).map((item, index) => (
                  <div key={index} className="order-item-preview">
                    <span>{item.name}</span>
                    <span>× {item.quantity}</span>
                  </div>
                ))}
                {order.items.length > 2 && (
                  <p className="more-items">+{order.items.length - 2} more items</p>
                )}
              </div>
              
              <div className="order-card-footer">
                <span className="order-total">${order.total.toFixed(2)}</span>
                <button 
                  onClick={() => navigate(`/order-confirmation/${order.id}`)}
                  className="view-order-btn"
                >
                  View Order
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LoginPage() {
  const { login, isAuthenticated } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(formData);
      addToast('Login successful!', 'success');
      navigate('/');
    } catch (error) {
      addToast(error.message || 'Login failed', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Login</h1>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input 
              type="email" 
              id="email" 
              name="email" 
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              name="password" 
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <p className="auth-redirect">
          Don't have an account? <button onClick={() => navigate('/register')}>Register</button>
        </p>
      </div>
    </div>
  );
}

function RegisterPage() {
  const { register, isAuthenticated } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      addToast('Passwords do not match', 'error');
      return;
    }
    
    setLoading(true);
    
    try {
      const { username, email, password } = formData;
      await register({ username, email, password });
      addToast('Registration successful!', 'success');
      navigate('/');
    } catch (error) {
      addToast(error.message || 'Registration failed', 'error');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-page">
      <div className="auth-container">
        <h1>Register</h1>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input 
              type="text" 
              id="username" 
              name="username" 
              value={formData.username}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input 
              type="email" 
              id="email" 
              name="email" 
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              name="password" 
              value={formData.password}
              onChange={handleChange}
              required
              minLength={6}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input 
              type="password" 
              id="confirmPassword" 
              name="confirmPassword" 
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              minLength={6}
            />
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        
        <p className="auth-redirect">
          Already have an account? <button onClick={() => navigate('/login')}>Login</button>
        </p>
      </div>
    </div>
  );
}

// Navigation component
function Navbar() {
  const { user, isAuthenticated, logout } = React.useContext(AuthContext);
  const { cart } = React.useContext(CartContext);
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };
  
  return (
    <nav className="navbar">
      <div className="navbar-brand" onClick={() => navigate('/')}>
        <h1>ShopCart</h1>
      </div>
      
      <div className="navbar-menu">
        <button onClick={() => navigate('/')}>Products</button>
        {isAuthenticated && <button onClick={() => navigate('/orders')}>Orders</button>}
      </div>
      
      <div className="navbar-end">
        {isAuthenticated ? (
          <>
            <div className="user-info">
              <span>Hi, {user.username}</span>
            </div>
            <button className="cart-icon" onClick={() => navigate('/cart')}>
              <span>🛒</span>
              {cart.items.length > 0 && (
                <span className="cart-badge">{cart.items.length}</span>
              )}
            </button>
            <button className="logout-btn" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <button className="login-btn" onClick={() => navigate('/login')}>Login</button>
        )}
      </div>
    </nav>
  );
}

// Toast context
const ToastContext = React.createContext(null);

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  
  const addToast = (message, type = 'info') => {
    const newToast = {
      id: Date.now(),
      message,
      type
    };
    setToasts(prev => [...prev, newToast]);
  };
  
  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };
  
  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

// Router context and components
const Router = React.createContext(null);

function RouterProvider({ children }) {
  const [location, setLocation] = useState(window.location.pathname);
  const [params, setParams] = useState({});
  
  useEffect(() => {
    const handleLocationChange = () => {
      setLocation(window.location.pathname);
      
      // Extract route params if needed
      const pathParts = window.location.pathname.split('/');
      const newParams = {};
      
      // Simple example for /order-confirmation/:orderId
      if (pathParts[1] === 'order-confirmation' && pathParts[2]) {
        newParams.orderId = pathParts[2];
      }
      
      setParams(newParams);
    };
    
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, []);
  
  const navigate = useCallback((to) => {
    window.history.pushState({}, '', to);
    setLocation(to);
    
    // Extract route params if needed
    const pathParts = to.split('/');
    const newParams = {};
    
    // Simple example for /order-confirmation/:orderId
    if (pathParts[1] === 'order-confirmation' && pathParts[2]) {
      newParams.orderId = pathParts[2];
    }
    
    setParams(newParams);
  }, []);
  
  return (
    <Router.Provider value={{ location, navigate, params }}>
      {children}
    </Router.Provider>
  );
}

function useNavigate() {
  const { navigate } = React.useContext(Router);
  return navigate;
}

function useParams() {
  const { params } = React.useContext(Router);
  return params;
}

// Main App component
function App() {
  const { location } = React.useContext(Router);
  
  // Main router logic
  const renderPage = () => {
    if (location === '/') {
      return <HomePage />;
    }
    if (location === '/cart') {
      return <CartPage />;
    }
    if (location === '/checkout') {
      return <CheckoutPage />;
    }
    if (location.startsWith('/order-confirmation/')) {
      return <OrderConfirmationPage />;
    }
    if (location === '/orders') {
      return <OrdersPage />;
    }
    if (location === '/login') {
      return <LoginPage />;
    }
    if (location === '/register') {
      return <RegisterPage />;
    }
    
    // 404 page
    return (
      <div className="not-found">
        <h1>404 - Page Not Found</h1>
        <p>The page you are looking for does not exist.</p>
        <button onClick={() => useNavigate()('/')}>Go Home</button>
      </div>
    );
  };
  
  return (
    <div className="app-container">
      <Navbar />
      <main className="main-content">
        {renderPage()}
      </main>
      <footer className="footer">
        <p>© 2023 ShopCart. All rights reserved.</p>
      </footer>
    </div>
  );
}

// Wrap the app with all providers
function AppWithProviders() {
  return (
    <RouterProvider>
      <ToastProvider>
        <AuthProvider>
          <CartProvider>
            <App />
          </CartProvider>
        </AuthProvider>
      </ToastProvider>
    </RouterProvider>
  );
}

// Mount the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<AppWithProviders />);

export default AppWithProviders;

    

