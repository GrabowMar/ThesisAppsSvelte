// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// 2. State Management
const App = () => {
  const [devices, setDevices] = useState([]);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await axios.get('http://localhost:5111/devices');
      setDevices(response.data);
    } catch (error) {
      console.error('Error fetching devices:', error);
    }
  };

  const addDevice = async (device) => {
    try {
      const response = await axios.post('http://localhost:5111/devices', device);
      setDevices([...devices, response.data]);
    } catch (error) {
      console.error('Error adding device:', error);
    }
  };

  const deleteDevice = async (deviceId) => {
    try {
      await axios.delete(`http://localhost:5111/devices/${deviceId}`);
      setDevices(devices.filter(device => device.id !== deviceId));
    } catch (error) {
      console.error('Error deleting device:', error);
    }
  };

  const sendCommand = async (deviceId, command) => {
    try {
      await axios.post(`http://localhost:5111/devices/${deviceId}/command`, { command });
      fetchDevices();
    } catch (error) {
      console.error('Error sending command:', error);
    }
  };

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/devices">Devices</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/devices" element={<DeviceList devices={devices} addDevice={addDevice} deleteDevice={deleteDevice} sendCommand={sendCommand} />} />
      </Routes>
    </Router>
  );
};

const Home = () => <h1>Welcome to the IoT Controller System</h1>;

const DeviceList = ({ devices, addDevice, deleteDevice, sendCommand }) => {
  const [newDevice, setNewDevice] = useState({ id: Date.now(), name: '', status: 'unknown' });
  const [command, setCommand] = useState('');

  const handleAddDevice = () => {
    addDevice(newDevice);
    setNewDevice({ id: Date.now(), name: '', status: 'unknown' });
  };

  const handleSendCommand = (deviceId) => {
    sendCommand(deviceId, command);
    setCommand('');
  };

  return (
    <div>
      <h2>Devices</h2>
      <input type="text" value={newDevice.name} onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })} placeholder="Device Name" />
      <button onClick={handleAddDevice}>Add Device</button>
      <ul>
        {devices.map(device => (
          <li key={device.id}>
            {device.name} - {device.status}
            <button onClick={() => deleteDevice(device.id)}>Delete</button>
            <input type="text" value={command} onChange={(e) => setCommand(e.target.value)} placeholder="Command" />
            <button onClick={() => handleSendCommand(device.id)}>Send Command</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

// 3. Lifecycle Functions
// 4. Event Handlers
// 5. API Calls

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
