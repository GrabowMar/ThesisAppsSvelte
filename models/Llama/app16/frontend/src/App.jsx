import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [devices, setDevices] = useState({});
  const [deviceStatus, setDeviceStatus] = useState({});
  const [token, setToken] = useState(null);

  useEffect(() => {
    axios.get('/api/devices')
      .then(response => {
        setDevices(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleLogin = (username, password) => {
    axios.post('/api/login', { username, password })
      .then(response => {
        setToken(response.data.token);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleUpdateDeviceStatus = (device_id, status) => {
    axios.put(`/api/devices/${device_id}/status`, { status })
      .then(response => {
        setDeviceStatus(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <h1>IoT Device Management</h1>
      {token ? (
        <div>
          <h2>Devices</h2>
          <ul>
            {Object.keys(devices).map(device_id => (
              <li key={device_id}>
                {device_id} - {devices[device_id].status}
                <button onClick={() => handleUpdateDeviceStatus(device_id, 'online')}>Online</button>
                <button onClick={() => handleUpdateDeviceStatus(device_id, 'offline')}>Offline</button>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div>
          <h2>Login</h2>
          <form>
            <label>Username:</label>
            <input type="text" />
            <label>Password:</label>
            <input type="password" />
            <button onClick={() => handleLogin('admin', 'password123')}>Login</button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;
