import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [devices, setDevices] = useState([]);
  const [newDeviceName, setNewDeviceName] = useState('');

  // Fetch devices from backend
  useEffect(() => {
    fetch('http://localhost:5191/api/devices')
      .then((response) => response.json())
      .then((data) => setDevices(data))
      .catch((error) => console.error('Error fetching devices:', error));
  }, []);

  // Toggle device status
  const toggleDeviceStatus = (deviceId, currentStatus) => {
    const newStatus = currentStatus === 'on' ? 'off' : 'on';
    fetch(`http://localhost:5191/api/devices/${deviceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
      .then((response) => response.json())
      .then((updatedDevice) => {
        setDevices((prevDevices) =>
          prevDevices.map((device) =>
            device.id === updatedDevice.id ? updatedDevice : device
          )
        );
      })
      .catch((error) => console.error('Error updating device:', error));
  };

  // Add a new device
  const addDevice = () => {
    if (!newDeviceName.trim()) return;
    fetch('http://localhost:5191/api/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newDeviceName }),
    })
      .then((response) => response.json())
      .then((newDevice) => {
        setDevices((prevDevices) => [...prevDevices, newDevice]);
        setNewDeviceName('');
      })
      .catch((error) => console.error('Error adding device:', error));
  };

  // Delete a device
  const deleteDevice = (deviceId) => {
    fetch(`http://localhost:5191/api/devices/${deviceId}`, {
      method: 'DELETE',
    })
      .then(() => {
        setDevices((prevDevices) =>
          prevDevices.filter((device) => device.id !== deviceId)
        );
      })
      .catch((error) => console.error('Error deleting device:', error));
  };

  return (
    <div className="app">
      <h1>IoT Device Controller</h1>
      <div className="add-device">
        <input
          type="text"
          placeholder="Enter device name"
          value={newDeviceName}
          onChange={(e) => setNewDeviceName(e.target.value)}
        />
        <button onClick={addDevice}>Add Device</button>
      </div>
      <div className="device-list">
        {devices.map((device) => (
          <div key={device.id} className="device-card">
            <h3>{device.name}</h3>
            <p>Status: {device.status}</p>
            <button onClick={() => toggleDeviceStatus(device.id, device.status)}>
              Turn {device.status === 'on' ? 'Off' : 'On'}
            </button>
            <button onClick={() => deleteDevice(device.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
