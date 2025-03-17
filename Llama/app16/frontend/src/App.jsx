// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [status, setStatus] = useState("");
  const [command, setCommand] = useState("");
  const [data, setData] = useState("");
  const [automationData, setAutomationData] = useState({});

  useEffect(() => {
    fetch('http://localhost:5031/devices')
      .then(response => response.json())
      .then(data => setDevices(data));
  }, []);

  const handleDeviceSelect = (device) => {
    setSelectedDevice(device);
    fetch(`http://localhost:5031/devices/${device.id}/status`)
      .then(response => response.json())
      .then(data => setStatus(data.status));
  };

  const handleCommandSend = () => {
    fetch(`http://localhost:5031/devices/${selectedDevice.id}/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: command })
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleDataSend = () => {
    fetch(`http://localhost:5031/devices/${selectedDevice.id}/data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: data })
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  const handleAutomation = () => {
    fetch('http://localhost:5031/automate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(automationData)
    })
      .then(response => response.json())
      .then(data => console.log(data));
  };

  return (
    <div className="App">
      <h1>IoT Controller</h1>
      <div>
        <h2>Devices</h2>
        <ul>
          {devices.map(device => (
            <li key={device.id} onClick={() => handleDeviceSelect(device)}>
              {device.name}
            </li>
          ))}
        </ul>
      </div>
      {selectedDevice && (
        <div>
          <h2>Selected Device: {selectedDevice.name}</h2>
          <p>Status: {status}</p>
          <input type="text" value={command} onChange={(e) => setCommand(e.target.value)} placeholder="Enter command" />
          <button onClick={handleCommandSend}>Send Command</button>
          <input type="text" value={data} onChange={(e) => setData(e.target.value)} placeholder="Enter data" />
          <button onClick={handleDataSend}>Send Data</button>
          <button onClick={handleAutomation}>Automate</button>
        </div>
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
