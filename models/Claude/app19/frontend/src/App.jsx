import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5357/api';

// Authentication Service
const AuthService = {
  login: async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }
    
    const data = await response.json();
    localStorage.setItem('user', JSON.stringify({
      username: data.username,
      email: data.email,
      token: data.token
    }));
    
    return data;
  },
  
  register: async (username, email, password) => {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }
    
    return await response.json();
  },
  
  logout: () => {
    localStorage.removeItem('user');
  },
  
  getCurrentUser: () => {
    return JSON.parse(localStorage.getItem('user'));
  },
  
  authHeader: () => {
    const user = JSON.parse(localStorage.getItem('user'));
    
    if (user && user.token) {
      return { 'Authorization': `Bearer ${user.token}` };
    } else {
      return {};
    }
  }
};

// Wallet Service
const WalletService = {
  getBalance: async () => {
    const response = await fetch(`${API_BASE_URL}/wallet/balance`, {
      headers: { ...AuthService.authHeader() }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch balance');
    }
    
    return await response.json();
  },
  
  getAddress: async () => {
    const response = await fetch(`${API_BASE_URL}/wallet/address`, {
      headers: { ...AuthService.authHeader() }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch address');
    }
    
    return await response.json();
  },
  
  sendCrypto: async (toAddress, amount) => {
    const response = await fetch(`${API_BASE_URL}/transactions/send`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...AuthService.authHeader()
      },
      body: JSON.stringify({ to_address: toAddress, amount })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Transaction failed');
    }
    
    return await response.json();
  },
  
  getTransactionHistory: async () => {
    const response = await fetch(`${API_BASE_URL}/transactions/history`, {
      headers: { ...AuthService.authHeader() }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch transaction history');
    }
    
    return await response.json();
  },
  
  getAddresses: async () => {
    const response = await fetch(`${API_BASE_URL}/addresses`, {
      headers: { ...AuthService.authHeader() }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to fetch addresses');
    }
    
    return await response.json();
  },
  
  addAddress: async (address, label) => {
    const response = await fetch(`${API_BASE_URL}/addresses`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...AuthService.authHeader()
      },
      body: JSON.stringify({ address, label })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to add address');
    }
    
    return await response.json();
  },
  
  deleteAddress: async (address) => {
    const response = await fetch(`${API_BASE_URL}/addresses/${address}`, {
      method: 'DELETE',
      headers: { ...AuthService.authHeader() }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to delete address');
    }
    
    return await response.json();
  }
};

// UI Components
const LoginForm = ({ onLogin, onNavigate }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await AuthService.login(username, password);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-form">
      <h2>Login to Your Wallet</h2>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleLogin}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p className="form-footer">
        Don't have an account?{' '}
        <button className="btn-link" onClick={() => onNavigate('register')}>
          Register
        </button>
      </p>
    </div>
  );
};

const RegisterForm = ({ onNavigate }) => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');
    
    if (password !== confirmPassword) {
      setError("Passwords don't match");
      setLoading(false);
      return;
    }
    
    try {
      await AuthService.register(username, email, password);
      setSuccess('Registration successful! You can now login.');
      setTimeout(() => onNavigate('login'), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="auth-form">
      <h2>Create Your Wallet</h2>
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <p className="form-footer">
        Already have an account?{' '}
        <button className="btn-link" onClick={() => onNavigate('login')}>
          Login
        </button>
      </p>
    </div>
  );
};

const Dashboard = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState('wallet');
  const [walletInfo, setWalletInfo] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState({
    wallet: false,
    transactions: false,
    addresses: false
  });
  const [error, setError] = useState({
    wallet: '',
    transactions: '',
    addresses: ''
  });
  
  const user = AuthService.getCurrentUser();
  
  const fetchWalletInfo = async () => {
    setLoading({ ...loading, wallet: true });
    try {
      const [balanceData, addressData] = await Promise.all([
        WalletService.getBalance(),
        WalletService.getAddress()
      ]);
      
      setWalletInfo({
        balance: balanceData.balance,
        address: addressData.address
      });
      setError({ ...error, wallet: '' });
    } catch (err) {
      setError({ ...error, wallet: err.message });
    } finally {
      setLoading({ ...loading, wallet: false });
    }
  };
  
  const fetchTransactions = async () => {
    setLoading({ ...loading, transactions: true });
    try {
      const data = await WalletService.getTransactionHistory();
      setTransactions(data.transactions);
      setError({ ...error, transactions: '' });
    } catch (err) {
      setError({ ...error, transactions: err.message });
    } finally {
      setLoading({ ...loading, transactions: false });
    }
  };
  
  const fetchAddresses = async () => {
    setLoading({ ...loading, addresses: true });
    try {
      const data = await WalletService.getAddresses();
      setAddresses(data.addresses);
      setError({ ...error, addresses: '' });
    } catch (err) {
      setError({ ...error, addresses: err.message });
    } finally {
      setLoading({ ...loading, addresses: false });
    }
  };
  
  const handleLogout = () => {
    AuthService.logout();
    onLogout();
  };
  
  // Fetch data based on active tab
  useEffect(() => {
    if (activeTab === 'wallet' || activeTab === 'send') {
      fetchWalletInfo();
    } else if (activeTab === 'transactions') {
      fetchTransactions();
    } else if (activeTab === 'addresses') {
      fetchAddresses();
    }
  }, [activeTab]);
  
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Crypto Wallet</h1>
        <div className="user-info">
          <span>Welcome, {user.username}</span>
          <button onClick={handleLogout} className="btn-secondary">Logout</button>
        </div>
      </header>
      
      <nav className="dashboard-nav">
        <button 
          className={`nav-tab ${activeTab === 'wallet' ? 'active' : ''}`} 
          onClick={() => setActiveTab('wallet')}
        >
          Wallet
        </button>
        <button 
          className={`nav-tab ${activeTab === 'send' ? 'active' : ''}`} 
          onClick={() => setActiveTab('send')}
        >
          Send
        </button>
        <button 
          className={`nav-tab ${activeTab === 'transactions' ? 'active' : ''}`} 
          onClick={() => setActiveTab('transactions')}
        >
          Transactions
        </button>
        <button 
          className={`nav-tab ${activeTab === 'addresses' ? 'active' : ''}`} 
          onClick={() => setActiveTab('addresses')}
        >
          Addresses
        </button>
      </nav>
      
      <div className="dashboard-content">
        {activeTab === 'wallet' && (
          <WalletTab 
            walletInfo={walletInfo}
            loading={loading.wallet}
            error={error.wallet}
            onRefresh={fetchWalletInfo}
          />
        )}
        
        {activeTab === 'send' && (
          <SendTab 
            walletInfo={walletInfo}
            addresses={addresses}
            loading={loading.wallet}
            error={error.wallet}
            onComplete={() => {
              fetchWalletInfo();
              fetchTransactions();
            }}
          />
        )}
        
        {activeTab === 'transactions' && (
          <TransactionsTab 
            transactions={transactions}
            loading={loading.transactions}
            error={error.transactions}
            onRefresh={fetchTransactions}
          />
        )}
        
        {activeTab === 'addresses' && (
          <AddressesTab 
            addresses={addresses}
            loading={loading.addresses}
            error={error.addresses}
            onRefresh={fetchAddresses}
            onAddAddress={async (address, label) => {
              try {
                await WalletService.addAddress(address, label);
                fetchAddresses();
              } catch (err) {
                setError({ ...error, addresses: err.message });
              }
            }}
            onDeleteAddress={async (address) => {
              try {
                await WalletService.deleteAddress(address);
                fetchAddresses();
              } catch (err) {
                setError({ ...error, addresses: err.message });
              }
            }}
          />
        )}
      </div>
    </div>
  );
};

const WalletTab = ({ walletInfo, loading, error, onRefresh }) => (
  <div className="wallet-tab">
    <h2>Your Wallet</h2>
    {loading ? (
      <div className="spinner">Loading...</div>
    ) : error ? (
      <div className="error-message">{error}</div>
    ) : walletInfo ? (
      <div className="wallet-info">
        <div className="wallet-card">
          <div className="wallet-balance">
            <span className="balance-label">Balance</span>
            <span className="balance-value">{walletInfo.balance.toFixed(4)} ETH</span>
          </div>
          
          <div className="wallet-address">
            <span className="address-label">Address</span>
            <div className="address-value">
              <span className="address">{walletInfo.address}</span>
              <button 
                className="btn-icon" 
                onClick={() => {
                  navigator.clipboard.writeText(walletInfo.address);
                  alert('Address copied to clipboard!');
                }}
              >
                📋
              </button>
            </div>
          </div>
          
          <button onClick={onRefresh} className="btn-secondary">
            Refresh Balance
          </button>
        </div>
      </div>
    ) : (
      <div className="no-data">Wallet information not available</div>
    )}
  </div>
);

const SendTab = ({ walletInfo, addresses, loading, error, onComplete }) => {
  const [toAddress, setToAddress] = useState('');
  const [customAddress, setCustomAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [sendError, setSendError] = useState('');
  const [sendSuccess, setSendSuccess] = useState('');
  const [sendLoading, setSendLoading] = useState(false);
  const [useCustomAddress, setUseCustomAddress] = useState(true);
  
  const handleAddressChange = (e) => {
    setToAddress(e.target.value);
    setUseCustomAddress(e.target.value === 'custom');
  };
  
  const handleSend = async (e) => {
    e.preventDefault();
    setSendLoading(true);
    setSendError('');
    setSendSuccess('');
    
    const targetAddress = useCustomAddress ? customAddress : toAddress;
    
    if (!targetAddress) {
      setSendError('Please provide a valid address');
      setSendLoading(false);
      return;
    }
    
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
      setSendError('Please provide a valid amount');
      setSendLoading(false);
      return;
    }
    
    if (parseFloat(amount) > walletInfo.balance) {
      setSendError('Insufficient balance');
      setSendLoading(false);
      return;
    }
    
    try {
      const result = await WalletService.sendCrypto(targetAddress, parseFloat(amount));
      setSendSuccess(`Transaction completed! ID: ${result.transaction_id}`);
      setAmount('');
      setToAddress('');
      setCustomAddress('');
      onComplete();
    } catch (err) {
      setSendError(err.message);
    } finally {
      setSendLoading(false);
    }
  };
  
  return (
    <div className="send-tab">
      <h2>Send Crypto</h2>
      {loading ? (
        <div className="spinner">Loading wallet info...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : walletInfo ? (
        <div className="send-form-container">
          <div className="wallet-balance-info">
            <span>Available Balance: </span>
            <span className="highlighted">{walletInfo.balance.toFixed(4)} ETH</span>
          </div>
          
          {sendError && <div className="error-message">{sendError}</div>}
          {sendSuccess && <div className="success-message">{sendSuccess}</div>}
          
          <form onSubmit={handleSend} className="send-form">
            <div className="form-group">
              <label htmlFor="toAddress">Send To</label>
              <select id="toAddress" value={toAddress} onChange={handleAddressChange}>
                <option value="" disabled>Select an address</option>
                <option value="custom">Enter custom address</option>
                {addresses.map((addr) => (
                  <option key={addr.address} value={addr.address}>
                    {addr.label} ({addr.address.substring(0, 6)}...{addr.address.substring(addr.address.length - 4)})
                  </option>
                ))}
              </select>
              
              {useCustomAddress && (
                <input
                  type="text"
                  className="custom-address"
                  placeholder="Enter wallet address (0x...)"
                  value={customAddress}
                  onChange={(e) => setCustomAddress(e.target.value)}
                  required
                />
              )}
            </div>
            
            <div className="form-group">
              <label htmlFor="amount">Amount (ETH)</label>
              <input
                type="number"
                id="amount"
                step="0.0001"
                min="0.0001"
                max={walletInfo.balance}
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={sendLoading} className="btn-primary">
              {sendLoading ? 'Processing...' : 'Send'}
            </button>
          </form>
        </div>
      ) : (
        <div className="no-data">Wallet information not available</div>
      )}
    </div>
  );
};

const TransactionsTab = ({ transactions, loading, error, onRefresh }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="transactions-tab">
      <div className="tab-header">
        <h2>Transaction History</h2>
        <button onClick={onRefresh} className="btn-secondary">
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="spinner">Loading transactions...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : transactions && transactions.length > 0 ? (
        <div className="transactions-list">
          {transactions.map((tx) => (
            <div key={tx.id} className={`transaction-item ${tx.direction}`}>
              <div className="transaction-icon">
                {tx.direction === 'outgoing' ? '↑' : '↓'}
              </div>
              <div className="transaction-details">
                <div className="transaction-main">
                  <span className="transaction-type">
                    {tx.direction === 'outgoing' ? 'Sent' : 'Received'}
                  </span>
                  <span className="transaction-amount">
                    {tx.direction === 'outgoing' ? '-' : '+'}{tx.amount.toFixed(4)} ETH
                  </span>
                </div>
                <div className="transaction-meta">
                  <span className="transaction-date">{formatDate(tx.timestamp)}</span>
                  <span className="transaction-status">{tx.status}</span>
                </div>
                <div className="transaction-address">
                  {tx.direction === 'outgoing' 
                    ? `To: ${tx.to_address.substring(0, 10)}...${tx.to_address.substring(tx.to_address.length - 4)}`
                    : `From: ${tx.from_address.substring(0, 10)}...${tx.from_address.substring(tx.from_address.length - 4)}`}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-data">No transactions found</div>
      )}
    </div>
  );
};

const AddressesTab = ({ addresses, loading, error, onRefresh, onAddAddress, onDeleteAddress }) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAddress, setNewAddress] = useState('');
  const [newLabel, setNewLabel] = useState('');
  const [addError, setAddError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!newAddress.startsWith('0x') || newAddress.length !== 42) {
      setAddError('Please enter a valid Ethereum address (0x... format, 42 characters)');
      return;
    }
    
    try {
      await onAddAddress(newAddress, newLabel);
      setNewAddress('');
      setNewLabel('');
      setAddError('');
      setShowAddForm(false);
    } catch (err) {
      setAddError(err.message);
    }
  };
  
  return (
    <div className="addresses-tab">
      <div className="tab-header">
        <h2>Saved Addresses</h2>
        <div className="tab-actions">
          <button onClick={() => setShowAddForm(!showAddForm)} className="btn-secondary">
            {showAddForm ? 'Cancel' : 'Add Address'}
          </button>
          <button onClick={onRefresh} className="btn-secondary">
            Refresh
          </button>
        </div>
      </div>
      
      {showAddForm && (
        <div className="add-address-form">
          <h3>Add New Address</h3>
          {addError && <div className="error-message">{addError}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="newAddress">Address (0x...)</label>
              <input
                type="text"
                id="newAddress"
                value={newAddress}
                onChange={(e) => setNewAddress(e.target.value)}
                placeholder="0x..."
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="newLabel">Label</label>
              <input
                type="text"
                id="newLabel"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="e.g. My Exchange Wallet"
                required
              />
            </div>
            <button type="submit" className="btn-primary">
              Save Address
            </button>
          </form>
        </div>
      )}
      
      {loading ? (
        <div className="spinner">Loading addresses...</div>
      ) : error ? (
        <div className="error-message">{error}</div>
      ) : addresses && addresses.length > 0 ? (
        <div className="addresses-list">
          {addresses.map((addr) => (
            <div key={addr.address} className="address-item">
              <div className="address-info">
                <div className="address-label">{addr.label}</div>
                <div className="address-value">
                  <span>{addr.address}</span>
                  <button 
                    className="btn-icon" 
                    onClick={() => {
                      navigator.clipboard.writeText(addr.address);
                      alert('Address copied to clipboard!');
                    }}
                  >
                    📋
                  </button>
                </div>
              </div>
              <div className="address-actions">
                <button 
                  className="btn-delete" 
                  onClick={() => {
                    if (window.confirm(`Delete address "${addr.label}"?`)) {
                      onDeleteAddress(addr.address);
                    }
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-data">No saved addresses</div>
      )}
    </div>
  );
};

const App = () => {
  const [currentPage, setCurrentPage] = useState('login');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Check if user is already logged in
  useEffect(() => {
    const user = AuthService.getCurrentUser();
    if (user) {
      setIsAuthenticated(true);
    }
  }, []);
  
  const handleLogin = () => {
    setIsAuthenticated(true);
  };
  
  const handleLogout = () => {
    setIsAuthenticated(false);
    setCurrentPage('login');
  };
  
  const renderPage = () => {
    if (isAuthenticated) {
      return <Dashboard onLogout={handleLogout} />;
    }
    
    switch (currentPage) {
      case 'login':
        return <LoginForm onLogin={handleLogin} onNavigate={setCurrentPage} />;
      case 'register':
        return <RegisterForm onNavigate={setCurrentPage} />;
      default:
        return <LoginForm onLogin={handleLogin} onNavigate={setCurrentPage} />;
    }
  };
  
  return (
    <div className="app">
      {renderPage()}
    </div>
  );
};

// Mount the app to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;

