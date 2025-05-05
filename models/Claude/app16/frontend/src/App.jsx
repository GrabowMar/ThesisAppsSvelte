import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:5351/api';

// Helper Functions
const formatDate = (timestamp) => {
  const date = new Date(timestamp * 1000);
  return date.toLocaleString();
};

const setAuthToken = (token) => {
  if (token) {
    localStorage.setItem('token', token);
  } else {
    localStorage.removeItem('token');
  }
};

const getAuthToken = () => localStorage.getItem('token');

const api = {
  async request(endpoint, method = 'GET', data = null) {
    const token = getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      method,
      headers,
    };

    if (data) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
      const responseData = await response.json();

      if (!response.ok) {
        throw new Error(responseData.message || 'Something went wrong');
      }

      return responseData;
    } catch (error) {
      console.error('API request error:', error);
      throw error;
    }
  },

  login(credentials) {
    return this.request('/login', 'POST', credentials);
  },

  register(userData) {
    return this.request('/register', 'POST', userData);
  },

  getDashboard() {
    return this.request('/dashboard');
  },

  getDevices() {
    return this.request('/devices');
  },

  getDevice(id) {
    return this.request(`/devices/${id}`);
  },

  updateDevice(id, data) {
    return this.request(`/devices/${id}`, 'PUT', data);
  },

  controlDevice(id, command) {
    return this.request(`/devices/${id}/command`, 'POST', command);
  },

  addDevice(deviceData) {
    return this.request('/devices/add', 'POST', deviceData);
  },

  deleteDevice(id) {
    return this.request(`/devices/${id}`, 'DELETE');
  },

  getAutomations() {
    return this.request('/automations');
  },

  getAutomation(id) {
    return this.request(`/automations/${id}`);
  },

  createAutomation(data) {
    return this.request('/automations', 'POST', data);
  },

  updateAutomation(id, data) {
    return this.request(`/automations/${id}`, 'PUT', data);
  },

  deleteAutomation(id) {
    return this.request(`/automations/${id}`, 'DELETE');
  },
};

// Components
const Navbar = ({ user, onLogout }) => {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <span className="navbar-logo">🏠</span>
        <h1>IoT Controller</h1>
      </div>
      <div className="navbar-menu">
        {user && (
          <>
            <span className="navbar-user">Welcome, {user.name}</span>
            <button className="navbar-logout" onClick={onLogout}>Logout</button>
          </>
        )}
      </div>
    </nav>
  );
};

const Sidebar = ({ activePage, setActivePage }) => {
  return (
    <div className="sidebar">
      <div 
        className={`sidebar-item ${activePage === 'dashboard' ? 'active' : ''}`}
        onClick={() => setActivePage('dashboard')}
      >
        <span className="sidebar-icon">📊</span>
        <span className="sidebar-text">Dashboard</span>
      </div>
      <div 
        className={`sidebar-item ${activePage === 'devices' ? 'active' : ''}`}
        onClick={() => setActivePage('devices')}
      >
        <span className="sidebar-icon">💡</span>
        <span className="sidebar-text">Devices</span>
      </div>
      <div 
        className={`sidebar-item ${activePage === 'automations' ? 'active' : ''}`}
        onClick={() => setActivePage('automations')}
      >
        <span className="sidebar-icon">⚙️</span>
        <span className="sidebar-text">Automations</span>
      </div>
    </div>
  );
};

const LoginForm = ({ onLogin, navigateToRegister }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!email || !password) {
      setError('Email and password are required');
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.login({ email, password });
      if (response.authenticated) {
        setAuthToken(response.token);
        onLogin(response.user);
      } else {
        setError(response.message || 'Login failed');
      }
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <h2>Login to IoT Controller</h2>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <a href="#" onClick={navigateToRegister}>
              Register
            </a>
          </p>
          <p className="auth-demo">
            <small>Demo: admin@example.com / admin123</small>
          </p>
        </div>
      </div>
    </div>
  );
};

const RegisterForm = ({ onRegister, navigateToLogin }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    if (!name || !email || !password || !confirmPassword) {
      setError('All fields are required');
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.register({ name, email, password });
      if (response.registered) {
        navigateToLogin();
      } else {
        setError(response.message || 'Registration failed');
      }
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <h2>Register for IoT Controller</h2>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
            />
          </div>
          <button type="submit" className="auth-button" disabled={isLoading}>
            {isLoading ? 'Registering...' : 'Register'}
          </button>
        </form>
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <a href="#" onClick={navigateToLogin}>
              Login
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const data = await api.getDashboard();
        setDashboardData(data);
        setLoading(false);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) return <div className="loading">Loading dashboard data...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;
  if (!dashboardData) return <div className="error-message">No dashboard data available</div>;

  return (
    <div className="dashboard">
      <h2>Dashboard</h2>
      
      <div className="dashboard-cards">
        <div className="dashboard-card">
          <div className="card-content">
            <h3>Devices</h3>
            <div className="card-value">{dashboardData.device_summary.total}</div>
          </div>
          <div className="card-details">
            <div className="status-item">
              <span className="status-label online">Online:</span>
              <span className="status-value">{dashboardData.device_summary.online}</span>
            </div>
            <div className="status-item">
              <span className="status-label offline">Offline:</span>
              <span className="status-value">{dashboardData.device_summary.offline}</span>
            </div>
            <div className="status-item">
              <span className="status-label error">Error:</span>
              <span className="status-value">{dashboardData.device_summary.error}</span>
            </div>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-content">
            <h3>Automations</h3>
            <div className="card-value">{dashboardData.automations_count}</div>
          </div>
          <div className="card-details">
            <p>Active automations ready to run</p>
          </div>
        </div>

        <div className="dashboard-card">
          <div className="card-content">
            <h3>Device Types</h3>
          </div>
          <div className="card-details">
            {Object.entries(dashboardData.device_summary.types).map(([type, count]) => (
              <div className="status-item" key={type}>
                <span className="status-label">{type}:</span>
                <span className="status-value">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="dashboard-section">
        <h3>Recent Activity</h3>
        <div className="activity-list">
          {dashboardData.recent_activity.map(activity => (
            <div className="activity-item" key={activity.id}>
              <div className="activity-content">
                <span className="activity-device">{activity.device}</span>
                <span className="activity-action">{activity.action}</span>
              </div>
              <span className="activity-time">{formatDate(activity.timestamp)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const DeviceCard = ({ device, onControl, onDelete, onEdit }) => {
  const getStatusClass = (status) => {
    switch (status) {
      case 'online':
        return 'status-online';
      case 'offline':
        return 'status-offline';
      case 'error':
        return 'status-error';
      default:
        return '';
    }
  };

  const renderDeviceControls = () => {
    switch (device.type) {
      case 'light':
        return (
          <>
            <div className="device-control">
              <span>Power:</span>
              <button 
                className={`toggle-button ${device.state ? 'on' : 'off'}`}
                onClick={() => onControl(device.id, { property: 'state', value: !device.state })}
              >
                {device.state ? 'ON' : 'OFF'}
              </button>
            </div>
            {device.state && (
              <div className="device-control">
                <span>Brightness:</span>
                <input 
                  type="range" 
                  min="1" 
                  max="100" 
                  value={device.brightness}
                  onChange={(e) => onControl(device.id, { property: 'brightness', value: parseInt(e.target.value) })}
                />
                <span className="range-value">{device.brightness}%</span>
              </div>
            )}
          </>
        );
      case 'thermostat':
        return (
          <>
            <div className="device-control">
              <span>Current Temperature:</span>
              <span className="temperature-value">{device.temperature}°C</span>
            </div>
            <div className="device-control">
              <span>Target Temperature:</span>
              <div className="temperature-control">
                <button 
                  onClick={() => onControl(device.id, { 
                    property: 'target_temperature', 
                    value: Math.max(15, device.target_temperature - 0.5)
                  })}
                >
                  -
                </button>
                <span className="temperature-value">{device.target_temperature}°C</span>
                <button 
                  onClick={() => onControl(device.id, { 
                    property: 'target_temperature', 
                    value: Math.min(30, device.target_temperature + 0.5)
                  })}
                >
                  +
                </button>
              </div>
            </div>
          </>
        );
      case 'lock':
        return (
          <div className="device-control">
            <span>Lock Status:</span>
            <button 
              className={`toggle-button ${device.state ? 'on' : 'off'}`}
              onClick={() => onControl(device.id, { property: 'state', value: !device.state })}
            >
              {device.state ? 'LOCKED' : 'UNLOCKED'}
            </button>
          </div>
        );
      default:
        return <p>No controls available for this device type</p>;
    }
  };

  return (
    <div className="device-card">
      <div className="device-header">
        <div className="device-info">
          <h3>{device.name}</h3>
          <span className={`device-status ${getStatusClass(device.status)}`}>
            {device.status}
          </span>
        </div>
        <div className="device-actions">
          <button className="icon-button edit" onClick={() => onEdit(device)}>
            ✏️
          </button>
          <button className="icon-button delete" onClick={() => onDelete(device.id)}>
            🗑️
          </button>
        </div>
      </div>
      
      <div className="device-details">
        <div className="device-type">
          <span>Type:</span> 
          <span>{device.type}</span>
        </div>
        <div className="device-location">
          <span>Location:</span> 
          <span>{device.location}</span>
        </div>
        <div className="device-last-updated">
          <span>Last Updated:</span> 
          <span>{formatDate(device.last_updated)}</span>
        </div>
      </div>

      <div className="device-controls">
        {renderDeviceControls()}
      </div>
    </div>
  );
};

const DeviceForm = ({ device, onSubmit, onCancel }) => {
  const [name, setName] = useState(device ? device.name : '');
  const [type, setType] = useState(device ? device.type : 'light');
  const [location, setLocation] = useState(device ? device.location : '');
  const [error, setError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!name || !location) {
      setError('Name and location are required');
      return;
    }

    onSubmit({
      id: device ? device.id : null,
      name,
      type,
      location
    });
  };

  return (
    <div className="modal-overlay">
      <div className="device-form">
        <h2>{device ? 'Edit Device' : 'Add New Device'}</h2>
        {error && <div className="form-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Device Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Living Room Light"
              required
            />
          </div>
          
          {!device && (
            <div className="form-group">
              <label htmlFor="type">Device Type</label>
              <select
                id="type"
                value={type}
                onChange={(e) => setType(e.target.value)}
              >
                <option value="light">Light</option>
                <option value="thermostat">Thermostat</option>
                <option value="lock">Lock</option>
              </select>
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="location">Location</label>
            <input
              type="text"
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g., Living Room"
              required
            />
          </div>
          
          <div className="form-buttons">
            <button type="button" className="cancel-button" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="submit-button">
              {device ? 'Save Changes' : 'Add Device'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ConfirmDialog = ({ message, onConfirm, onCancel }) => {
  return (
    <div className="modal-overlay">
      <div className="confirm-dialog">
        <p>{message}</p>
        <div className="dialog-buttons">
          <button className="cancel-button" onClick={onCancel}>Cancel</button>
          <button className="confirm-button" onClick={onConfirm}>Confirm</button>
        </div>
      </div>
    </div>
  );
};

const DevicesPage = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingDevice, setEditingDevice] = useState(null);
  const [deletingDeviceId, setDeletingDeviceId] = useState(null);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const data = await api.getDevices();
      setDevices(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    // Set up polling for periodic updates
    const interval = setInterval(fetchDevices, 10000); // Every 10 seconds
    
    return () => clearInterval(interval); // Clean up on unmount
  }, []);

  const handleControlDevice = async (deviceId, command) => {
    try {
      const response = await api.controlDevice(deviceId, command);
      // Update the device in the local state
      setDevices(devices.map(device => 
        device.id === deviceId ? response.device : device
      ));
    } catch (err) {
      setError(`Failed to control device: ${err.message}`);
    }
  };

  const handleAddDevice = async (deviceData) => {
    try {
      await api.addDevice(deviceData);
      fetchDevices();
      setShowAddForm(false);
    } catch (err) {
      setError(`Failed to add device: ${err.message}`);
    }
  };

  const handleUpdateDevice = async (deviceData) => {
    try {
      await api.updateDevice(deviceData.id, deviceData);
      fetchDevices();
      setEditingDevice(null);
    } catch (err) {
      setError(`Failed to update device: ${err.message}`);
    }
  };

  const handleDeleteDevice = async () => {
    if (!deletingDeviceId) return;
    
    try {
      await api.deleteDevice(deletingDeviceId);
      fetchDevices();
      setDeletingDeviceId(null);
    } catch (err) {
      setError(`Failed to delete device: ${err.message}`);
    }
  };

  const handleDeviceSubmit = (deviceData) => {
    if (deviceData.id) {
      handleUpdateDevice(deviceData);
    } else {
      handleAddDevice(deviceData);
    }
  };

  if (loading && devices.length === 0) return <div className="loading">Loading devices...</div>;
  
  return (
    <div className="devices-page">
      <div className="page-header">
        <h2>Devices</h2>
        <button className="add-button" onClick={() => setShowAddForm(true)}>
          Add Device
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="devices-grid">
        {devices.length > 0 ? (
          devices.map(device => (
            <DeviceCard 
              key={device.id}
              device={device}
              onControl={handleControlDevice}
              onDelete={(id) => setDeletingDeviceId(id)}
              onEdit={(device) => setEditingDevice(device)}
            />
          ))
        ) : (
          <div className="no-devices">
            <p>No devices found. Add your first device to get started.</p>
          </div>
        )}
      </div>
      
      {showAddForm && (
        <DeviceForm 
          onSubmit={handleDeviceSubmit}
          onCancel={() => setShowAddForm(false)}
        />
      )}
      
      {editingDevice && (
        <DeviceForm 
          device={editingDevice}
          onSubmit={handleDeviceSubmit}
          onCancel={() => setEditingDevice(null)}
        />
      )}
      
      {deletingDeviceId && (
        <ConfirmDialog 
          message="Are you sure you want to delete this device?"
          onConfirm={handleDeleteDevice}
          onCancel={() => setDeletingDeviceId(null)}
        />
      )}
    </div>
  );
};

const AutomationCard = ({ automation, onEdit, onDelete, onToggle }) => {
  return (
    <div className="automation-card">
      <div className="automation-header">
        <h3>{automation.name}</h3>
        <div className="automation-actions">
          <button 
            className={`status-toggle ${automation.status === 'active' ? 'active' : 'inactive'}`}
            onClick={() => onToggle(automation.id, automation.status === 'active' ? 'inactive' : 'active')}
          >
            {automation.status === 'active' ? 'Active' : 'Inactive'}
          </button>
          <button className="icon-button edit" onClick={() => onEdit(automation)}>
            ✏️
          </button>
          <button className="icon-button delete" onClick={() => onDelete(automation.id)}>
            🗑️
          </button>
        </div>
      </div>
      
      <div className="automation-details">
        <div className="trigger-section">
          <h4>Trigger</h4>
          {automation.trigger.time && (
            <div className="trigger-detail">
              <span>Time:</span> {automation.trigger.time}
            </div>
          )}
          {automation.trigger.days && (
            <div className="trigger-detail">
              <span>Days:</span> {automation.trigger.days.join(', ')}
            </div>
          )}
        </div>
        
        <div className="actions-section">
          <h4>Actions</h4>
          {automation.actions.map((action, index) => (
            <div className="action-item" key={index}>
              {action.device_id}: {action.property} → {action.value.toString()}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AutomationForm = ({ automation, onSubmit, onCancel, devices }) => {
  const [name, setName] = useState(automation ? automation.name : '');
  const [triggerTime, setTriggerTime] = useState(
    automation && automation.trigger.time ? automation.trigger.time : '00:00'
  );
  const [triggerDays, setTriggerDays] = useState(
    automation && automation.trigger.days ? [...automation.trigger.days] : 
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  );
  const [actions, setActions] = useState(
    automation && automation.actions ? [...automation.actions] : []
  );
  const [error, setError] = useState(null);
  
  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  
  const handleDayToggle = (day) => {
    if (triggerDays.includes(day)) {
      setTriggerDays(triggerDays.filter(d => d !== day));
    } else {
      setTriggerDays([...triggerDays, day]);
    }
  };
  
  const addAction = () => {
    if (devices.length === 0) {
      setError('No devices available. Add devices first.');
      return;
    }
    
    // Default new action based on the first device
    const device = devices[0];
    let defaultProperty = 'state';
    let defaultValue = false;
    
    if (device.type === 'thermostat') {
      defaultProperty = 'target_temperature';
      defaultValue = 22;
    }
    
    setActions([...actions, {
      device_id: device.id,
      property: defaultProperty,
      value: defaultValue
    }]);
  };
  
  const updateAction = (index, field, value) => {
    const updatedActions = [...actions];
    updatedActions[index] = {
      ...updatedActions[index],
      [field]: value
    };
    
    // If device changed, update property and value too
    if (field === 'device_id') {
      const selectedDevice = devices.find(d => d.id === value);
      if (selectedDevice.type === 'thermostat') {
        updatedActions[index].property = 'target_temperature';
        updatedActions[index].value = 22;
      } else {
        updatedActions[index].property = 'state';
        updatedActions[index].value = false;
      }
    }
    
    setActions(updatedActions);
  };
  
  const removeAction = (index) => {
    setActions(actions.filter((_, i) => i !== index));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!name) {
      setError('Automation name is required');
      return;
    }
    
    if (actions.length === 0) {
      setError('At least one action is required');
      return;
    }
    
    if (triggerDays.length === 0) {
      setError('At least one day must be selected');
      return;
    }
    
    const automationData = {
      id: automation ? automation.id : null,
      name,
      trigger: {
        time: triggerTime,
        days: triggerDays
      },
      actions,
      status: automation ? automation.status : 'active'
    };
    
    onSubmit(automationData);
  };
  
  return (
    <div className="modal-overlay">
      <div className="automation-form">
        <h2>{automation ? 'Edit Automation' : 'Create Automation'}</h2>
        {error && <div className="form-error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Automation Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Night Mode"
              required
            />
          </div>
          
          <div className="form-section">
            <h3>Trigger</h3>
            <div className="form-group">
              <label htmlFor="triggerTime">Time</label>
              <input
                type="time"
                id="triggerTime"
                value={triggerTime}
                onChange={(e) => setTriggerTime(e.target.value)}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Days</label>
              <div className="days-selector">
                {weekdays.map(day => (
                  <button
                    type="button"
                    key={day}
                    className={`day-button ${triggerDays.includes(day) ? 'selected' : ''}`}
                    onClick={() => handleDayToggle(day)}
                  >
                    {day.substring(0, 3)}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <div className="form-section">
            <div className="section-header">
              <h3>Actions</h3>
              <button type="button" className="add-action-button" onClick={addAction}>
                Add Action
              </button>
            </div>
            
            {actions.length === 0 ? (
              <p className="no-actions">No actions added yet. Click "Add Action" to start.</p>
            ) : (
              <div className="actions-list">
                {actions.map((action, index) => {
                  const selectedDevice = devices.find(d => d.id === action.device_id);
                  
                  return (
                    <div className="action-form-group" key={index}>
                      <div className="action-header">
                        <h4>Action {index + 1}</h4>
                        <button
                          type="button"
                          className="remove-action-button"
                          onClick={() => removeAction(index)}
                        >
                          ❌
                        </button>
                      </div>
                      
                      <div className="action-fields">
                        <div className="form-group">
                          <label>Device</label>
                          <select
                            value={action.device_id}
                            onChange={(e) => updateAction(index, 'device_id', e.target.value)}
                          >
                            {devices.map(device => (
                              <option key={device.id} value={device.id}>
                                {device.name}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div className="form-group">
                          <label>Property</label>
                          {selectedDevice?.type === 'thermostat' ? (
                            <select
                              value={action.property}
                              onChange={(e) => updateAction(index, 'property', e.target.value)}
                            >
                              <option value="target_temperature">Temperature</option>
                            </select>
                          ) : (
                            <select
                              value={action.property}
                              onChange={(e) => updateAction(index, 'property', e.target.value)}
                            >
                              <option value="state">Power</option>
                              {selectedDevice?.type === 'light' && (
                                <option value="brightness">Brightness</option>
                              )}
                            </select>
                          )}
                        </div>
                        
                        <div className="form-group">
                          <label>Value</label>
                          {action.property === 'state' ? (
                            <select
                              value={action.value.toString()}
                              onChange={(e) => updateAction(index, 'value', e.target.value === 'true')}
                            >
                              <option value="true">{selectedDevice?.type === 'lock' ? 'Locked' : 'On'}</option>
                              <option value="false">{selectedDevice?.type === 'lock' ? 'Unlocked' : 'Off'}</option>
                            </select>
                          ) : action.property === 'brightness' ? (
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={action.value}
                              onChange={(e) => updateAction(index, 'value', parseInt(e.target.value))}
                            />
                          ) : (
                            <input
                              type="number"
                              min="15"
                              max="30"
                              step="0.5"
                              value={action.value}
                              onChange={(e) => updateAction(index, 'value', parseFloat(e.target.value))}
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
          
          <div className="form-buttons">
            <button type="button" className="cancel-button" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="submit-button">
              {automation ? 'Save Changes' : 'Create Automation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AutomationsPage = () => {
  const [automations, setAutomations] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingAutomation, setEditingAutomation] = useState(null);
  const [deletingAutomationId, setDeletingAutomationId] = useState(null);

  const fetchAutomations = async () => {
    try {
      const data = await api.getAutomations();
      setAutomations(data);
    } catch (err) {
      setError(err.message || 'Failed to load automations');
    }
  };

  const fetchDevices = async () => {
    try {
      const data = await api.getDevices();
      setDevices(data);
    } catch (err) {
      setError(err.message || 'Failed to load devices');
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      await Promise.all([fetchAutomations(), fetchDevices()]);
      setLoading(false);
    };

    fetchData();
  }, []);

  const handleCreateAutomation = async (automationData) => {
    try {
      await api.createAutomation(automationData);
      fetchAutomations();
      setShowAddForm(false);
    } catch (err) {
      setError(`Failed to create automation: ${err.message}`);
    }
  };

  const handleUpdateAutomation = async (automationData) => {
    try {
      await api.updateAutomation(automationData.id, automationData);
      fetchAutomations();
      setEditingAutomation(null);
    } catch (err) {
      setError(`Failed to update automation: ${err.message}`);
    }
  };

  const handleDeleteAutomation = async () => {
    if (!deletingAutomationId) return;
    
    try {
      await api.deleteAutomation(deletingAutomationId);
      fetchAutomations();
      setDeletingAutomationId(null);
    } catch (err) {
      setError(`Failed to delete automation: ${err.message}`);
    }
  };

  const handleToggleAutomation = async (id, status) => {
    try {
      await api.updateAutomation(id, { status });
      fetchAutomations();
    } catch (err) {
      setError(`Failed to toggle automation: ${err.message}`);
    }
  };

  const handleAutomationSubmit = (automationData) => {
    if (automationData.id) {
      handleUpdateAutomation(automationData);
    } else {
      handleCreateAutomation(automationData);
    }
  };

  if (loading) return <div className="loading">Loading automations...</div>;

  return (
    <div className="automations-page">
      <div className="page-header">
        <h2>Automations</h2>
        <button className="add-button" onClick={() => setShowAddForm(true)}>
          Create Automation
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="automations-grid">
        {automations.length > 0 ? (
          automations.map(automation => (
            <AutomationCard 
              key={automation.id}
              automation={automation}
              onEdit={(automation) => setEditingAutomation(automation)}
              onDelete={(id) => setDeletingAutomationId(id)}
              onToggle={handleToggleAutomation}
            />
          ))
        ) : (
          <div className="no-automations">
            <p>No automations found. Create your first automation to get started.</p>
          </div>
        )}
      </div>
      
      {showAddForm && (
        <AutomationForm 
          onSubmit={handleAutomationSubmit}
          onCancel={() => setShowAddForm(false)}
          devices={devices}
        />
      )}
      
      {editingAutomation && (
        <AutomationForm 
          automation={editingAutomation}
          onSubmit={handleAutomationSubmit}
          onCancel={() => setEditingAutomation(null)}
          devices={devices}
        />
      )}
      
      {deletingAutomationId && (
        <ConfirmDialog 
          message="Are you sure you want to delete this automation?"
          onConfirm={handleDeleteAutomation}
          onCancel={() => setDeletingAutomationId(null)}
        />
      )}
    </div>
  );
};

// Main App Component
const App = () => {
  const [user, setUser] = useState(null);
  const [authPage, setAuthPage] = useState('login');
  const [activePage, setActivePage] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for saved token and try to auto-login
    const token = getAuthToken();
    if (token) {
      // This would normally validate the token with server
      // For this example, we'll just assume it's valid if it exists
      setUser({
        name: 'Saved User',
        email: 'saved@example.com',
        role: 'user'
      });
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    setActivePage('dashboard');
  };

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />;
      case 'devices':
        return <DevicesPage />;
      case 'automations':
        return <AutomationsPage />;
      default:
        return <Dashboard />;
    }
  };

  const renderAuth = () => {
    if (authPage === 'login') {
      return (
        <LoginForm 
          onLogin={handleLogin} 
          navigateToRegister={() => setAuthPage('register')}
        />
      );
    } else {
      return (
        <RegisterForm 
          onRegister={() => setAuthPage('login')} 
          navigateToLogin={() => setAuthPage('login')}
        />
      );
    }
  };

  if (loading) {
    return <div className="app-loading">Loading application...</div>;
  }

  return (
    <div className="app">
      {user ? (
        <>
          <Navbar user={user} onLogout={handleLogout} />
          <div className="main-container">
            <Sidebar activePage={activePage} setActivePage={setActivePage} />
            <main className="content">
              {renderPage()}
            </main>
          </div>
        </>
      ) : (
        renderAuth()
      )}
    </div>
  );
};

// Mount the app to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(<App />);

export default App;

                  

