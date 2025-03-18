import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

const App = () => {
  const [devices, setDevices] = useState({});

  useEffect(() => {
    // Fetch initial device data (dummy implementation)
    setDevices({
      'device1': { device_id: 'device1', status: 'online', data: [], automation: '' },
      'device2': { device_id: 'device2', status: 'offline', data: [], automation: '' },
    });
  }, []);

  const registerDevice = async (deviceId) => {
    const response = await fetch('http://localhost:5111/device', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId }),
    });
    const data = await response.json();
    if (response.ok) {
      setDevices({ ...devices, [deviceId]: { device_id: deviceId, status: 'online', data: [], automation: '' } });
    } else {
      console.error(data.error);
    }
  };

  const getDeviceStatus = async (deviceId) => {
    const response = await fetch(`http://localhost:5111/device/${deviceId}/status`);
    const data = await response.json();
    if (response.ok) {
      setDevices({ ...devices, [deviceId]: { ...devices[deviceId], status: data.status } });
    } else {
      console.error(data.error);
    }
  };

  const handleCommand = async (deviceId, command) => {
    const response = await fetch(`http://localhost:5111/device/${deviceId}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    });
    const data = await response.json();
    if (response.ok) {
      setDevices({ ...devices, [deviceId]: { ...devices[deviceId], status: data.message } });
    } else {
      console.error(data.error);
    }
  };

  const processData = async (deviceId, data) => {
    const response = await fetch(`http://localhost:5111/device/${deviceId}/data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    });
    const result = await response.json();
    if (response.ok) {
      setDevices({ ...devices, [deviceId]: { ...devices[deviceId], data } });
    } else {
      console.error(result.error);
    }
  };

  const automateDevice = async (deviceId, rule) => {
    const response = await fetch(`http://localhost:5111/device/${deviceId}/automate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule }),
    });
    const data = await response.json();
    if (response.ok) {
      setDevices({ ...devices, [deviceId]: { ...devices[deviceId], automation: rule } });
    } else {
      console.error(data.error);
    }
  };

  return (
    <Router>
      <div className="App">
        <nav>
          <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/register">Register Device</Link></li>
            <li><Link to="/status">Device Status</Link></li>
            <li><Link to="/command">Command Handling</Link></li>
            <li><Link to="/data">Data Processing</Link></li>
            <li><Link to="/automate">Automation</Link></li>
          </ul>
        </nav>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/register" element={<RegisterDevice registerDevice={registerDevice} />} />
          <Route path="/status" element={<DeviceStatus devices={devices} getDeviceStatus={getDeviceStatus} />} />
          <Route path="/command" element={<CommandHandling devices={devices} handleCommand={handleCommand} />} />
          <Route path="/data" element={<DataProcessing devices={devices} processData={processData} />} />
          <Route path="/automate" element={<Automation devices={devices} automateDevice={automateDevice} />} />
        </Routes>
      </div>
    </Router>
  );
};

const Home = () => <h2>Welcome to the IoT Controller System</h2>;

const RegisterDevice = ({ registerDevice }) => {
  const [deviceId, setDeviceId] = useState('');

  const handleRegister = () => {
    registerDevice(deviceId);
    setDeviceId('');
  };

  return (
    <div>
      <h2>Register Device</h2>
      <input
        type="text"
        value={deviceId}
        onChange={(e) => setDeviceId(e.target.value)}
        placeholder="Device ID"
      />
      <button onClick={handleRegister}>Register</button>
    </div>
  );
};

const DeviceStatus = ({ devices, getDeviceStatus }) => {
  return (
    <div>
      <h2>Device Status</h2>
      {Object.keys(devices).map((deviceId) => (
        <div key={deviceId}>
          <h3>{deviceId}</h3>
          <p>Status: {devices[deviceId].status}</p>
          <button onClick={() => getDeviceStatus(deviceId)}>Refresh Status</button>
        </div>
      ))}
    </div>
  );
};

const CommandHandling = ({ devices, handleCommand }) => {
  const [deviceId, setDeviceId] = useState('');
  const [command, setCommand] = useState('');

  const handleSendCommand = () => {
    handleCommand(deviceId, command);
    setDeviceId('');
    setCommand('');
  };

  return (
    <div>
      <h2>Command Handling</h2>
      <input
        type="text"
        value={deviceId}
        onChange={(e) => setDeviceId(e.target.value)}
        placeholder="Device ID"
      />
      <input
        type="text"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        placeholder="Command"
      />
      <button onClick={handleSendCommand}>Send Command</button>
    </div>
  );
};

const DataProcessing = ({ devices, processData }) => {
  const [deviceId, setDeviceId] = useState('');
  const [data, setData] = useState('');

  const handleProcessData = () => {
    processData(deviceId, data);
    setDeviceId('');
    setData('');
  };

  return (
    <div>
      <h2>Data Processing</h2>
      <input
        type="text"
        value={deviceId}
        onChange={(e) => setDeviceId(e.target.value)}
        placeholder="Device ID"
      />
      <input
        type="text"
        value={data}
        onChange={(e) => setData(e.target.value)}
        placeholder="Data"
      />
      <button onClick={handleProcessData}>Process Data</button>
    </div>
  );
};

const Automation = ({ devices, automateDevice }) => {
  const [deviceId, setDeviceId] = useState('');
  const [rule, setRule] = useState('');

  const handleAutomate = () => {
    automateDevice(deviceId, rule);
    setDeviceId('');
    setRule('');
  };

  return (
    <div>
      <h2>Automation</h2>
      <input
        type="text"
        value={deviceId}
        onChange={(e) => setDeviceId(e.target.value)}
        placeholder="Device ID"
      />
      <input
        type="text"
        value={rule}
        onChange={(e) => setRule(e.target.value)}
        placeholder="Automation Rule"
      />
      <button onClick={handleAutomate}>Apply Automation</button>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
