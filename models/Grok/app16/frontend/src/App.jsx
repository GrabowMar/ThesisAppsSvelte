import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [devices, setDevices] = useState({});
  const [loggedIn, setLoggedIn] = useState(false);
  const [currentPage, setCurrentPage] = useState('login');

  useEffect(() => {
    if (loggedIn) {
      fetchDevices();
    }
  }, [loggedIn]);

  const fetchDevices = async () => {
    try {
      const response = await fetch('/api/devices');
      if (response.ok) {
        const data = await response.json();
        setDevices(data);
      } else {
        console.error('Failed to fetch devices');
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
    }
  };

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        setLoggedIn(true);
        setCurrentPage('dashboard');
      } else {
        alert('Invalid credentials');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', {
        method: 'POST',
      });
      if (response.ok) {
        setLoggedIn(false);
        setCurrentPage('login');
      } else {
        alert('Logout failed');
      }
    } catch (error) {
      console.error('Logout error:', error);
      alert('Logout failed');
    }
  };

  const handleDeviceStatusChange = async (deviceId, status) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (response.ok) {
        fetchDevices();
      } else {
        alert('Failed to update device status');
      }
    } catch (error) {
      console.error('Error updating device status:', error);
      alert('Failed to update device status');
    }
  };

  const handleSendCommand = async (deviceId, command) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      });
      if (response.ok) {
        alert('Command sent successfully');
      } else {
        alert('Failed to send command');
      }
    } catch (error) {
      console.error('Error sending command:', error);
      alert('Failed to send command');
    }
  };

  const renderLoginPage = () => (
    <div className="login-page">
      <h1>IoT Controller Login</h1>
      <input type="text" placeholder="Username" id="username" />
      <input type="password" placeholder="Password" id="password" />
      <button onClick={() => handleLogin(document.getElementById('username').value, document.getElementById('password').value)}>Login</button>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard">
      <h1>IoT Controller Dashboard</h1>
      <button onClick={handleLogout}>Logout</button>
      <div className="device-list">
        {Object.entries(devices).map(([deviceId, device]) => (
          <div key={deviceId} className="device-card">
            <h2>{deviceId}</h2>
            <p>Status: {device.status}</p>
            <p>Last Updated: {device.last_updated}</p>
            <button onClick={() => handleDeviceStatusChange(deviceId, device.status === 'on' ? 'off' : 'on')}>
              {device.status === 'on' ? 'Turn Off' : 'Turn On'}
            </button>
            <input type="text" placeholder="Command" id={`command-${deviceId}`} />
            <button onClick={() => handleSendCommand(deviceId, document.getElementById(`command-${deviceId}`).value)}>Send Command</button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="app">
      {currentPage === 'login' ? renderLoginPage() : renderDashboard()}
    </div>
  );
}

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
