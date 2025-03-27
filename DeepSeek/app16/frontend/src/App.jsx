import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [devices, setDevices] = useState([]);
  const [page, setPage] = useState("dashboard");

  // Fetch devices on mount
  useEffect(() => {
    fetch("/api/devices")
      .then((response) => response.json())
      .then(setDevices);
  }, []);

  // Toggle device status
  const toggleDeviceStatus = (deviceId, command) => {
    fetch(`/api/devices/${deviceId}/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.message) {
          setDevices((prevDevices) =>
            prevDevices.map((device) =>
              device.id === deviceId ? { ...device, status: command } : device
            )
          );
        }
      });
  };

  return (
    <main>
      <nav>
        <button onClick={() => setPage("dashboard")}>Dashboard</button>
        <button onClick={() => setPage("devices")}>Devices</button>
      </nav>

      {page === "dashboard" && (
        <div>
          <h1>IoT Dashboard</h1>
          <p>Welcome to the IoT Controller System.</p>
        </div>
      )}

      {page === "devices" && (
        <div>
          <h1>Device Management</h1>
          <ul>
            {devices.map((device) => (
              <li key={device.id}>
                <p>
                  {device.name} - Status: {device.status}
                </p>
                <button
                  onClick={() =>
                    toggleDeviceStatus(
                      device.id,
                      device.status === "on" ? "off" : "on"
                    )
                  }
                >
                  {device.status === "on" ? "Turn Off" : "Turn On"}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
};

// Mount the app
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
