// frontend/src/App.jsx

import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";

/**
 * Main React App
 * Handles routing logic for IoT Controller App
 */

const App = () => {
  // State Management (Device Management, Page View)
  const [devices, setDevices] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState("dashboard"); // Options: "dashboard", "deviceDetails"

  // Lifecycle Hook: Fetch Devices on Mount
  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await fetch("/api/devices");
      const data = await response.json();
      setDevices(data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching devices:", error);
      setLoading(false);
    }
  };

  const handleDeviceSelect = async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}`);
      const data = await response.json();
      setSelectedDevice(data.device);
      setView("deviceDetails");
    } catch (error) {
      console.error("Error fetching device details:", error);
    }
  };

  const handleToggleDevice = async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/toggle`, {
        method: "POST",
      });
      const result = await response.json();
      console.log(result.message);
      fetchDevices(); // Refresh device states
    } catch (error) {
      console.error("Error toggling device:", error);
    }
  };

  // Render Views: Main Dashboard or Device Details
  if (loading) return <div className="loading">Loading devices...</div>;

  return (
    <div className="app-container">
      <header>
        <h1>IoT Controller System</h1>
        {view === "deviceDetails" && (
          <button onClick={() => setView("dashboard")}>Back to Dashboard</button>
        )}
      </header>

      {view === "dashboard" && (
        <div className="dashboard">
          <h2>Device Dashboard</h2>
          {devices.map((device) => (
            <div key={device.id} className="device-card">
              <h3>{device.name}</h3>
              <p>Status: {device.status}</p>
              <button onClick={() => handleDeviceSelect(device.id)}>View Details</button>
              <button onClick={() => handleToggleDevice(device.id)}>
                {device.status === "active" ? "Deactivate" : "Activate"}
              </button>
            </div>
          ))}
        </div>
      )}

      {view === "deviceDetails" && selectedDevice && (
        <div className="device-details">
          <h2>{selectedDevice.name}</h2>
          <p>Status: {selectedDevice.status}</p>
          <pre>{JSON.stringify(selectedDevice.data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

// Mount to DOM
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
