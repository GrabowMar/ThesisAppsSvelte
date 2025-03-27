import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [devices, setDevices] = useState({});
    const [currentPage, setCurrentPage] = useState('dashboard'); // Initial page
    const [loginStatus, setLoginStatus] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loginError, setLoginError] = useState('');


    useEffect(() => {
        if(loginStatus) {
            fetchDevices();
        }
    }, [loginStatus]);

    const fetchDevices = async () => {
        try {
            const response = await fetch('/api/devices');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setDevices(data);
        } catch (error) {
            console.error("Could not fetch devices:", error);
            // Optionally set an error state to display an error message
        }
    };

    const handleControl = async (deviceId, command) => {
        try {
            const response = await fetch(`/api/devices/${deviceId}/control`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: command })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log(result.message);

            // Refresh device data after control action
            fetchDevices();
        } catch (error) {
            console.error("Could not control device:", error);
            // Optionally set an error state to display an error message
        }
    };

    const handleStatusUpdate = async (deviceId, newStatus) => {
        try {
            const response = await fetch(`/api/devices/${deviceId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log(result.message);

            // Refresh device data after status update
            fetchDevices();
        } catch (error) {
            console.error("Could not update status:", error);
        }
    };

    const renderDeviceList = () => {
        return (
            <div>
                <h2>Device List</h2>
                <ul>
                    {Object.entries(devices).map(([deviceId, device]) => (
                        <li key={deviceId}>
                            <strong>{device.name} ({deviceId})</strong>
                            <p>Status: {device.status}</p>
                            {deviceId === "device1" && (
                                <div>
                                    <p>Temperature: {device.temperature}°C</p>
                                    <p>Humidity: {device.humidity}%</p>
                                    <button onClick={() => handleControl(deviceId, "get_reading")}>Get Reading</button>
                                </div>
                            )}
                            {deviceId === "device2" && (
                                <div>
                                    <p>Power: {device.power}</p>
                                    <button onClick={() => handleControl(deviceId, "toggle")}>Toggle Power</button>
                                </div>
                            )}
                            <button onClick={() => handleStatusUpdate(deviceId, device.status === "online" ? "offline" : "online")}>
                                Change Status
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
        );
    };

    const handleLogin = async () => {
         try {
             const response = await fetch('/api/login', {
                  method: 'POST',
                  headers: {
                       'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ username: username, password: password })
             });

             if (response.ok) {
                 setLoginStatus(true);
                 setLoginError('');
             } else {
                 setLoginError('Invalid credentials');
             }
         } catch (error) {
             setLoginError('Login failed');
         }
    };

    const renderLoginPage = () => {
        return (
            <div className="login-container">
                <h2>Login</h2>
                {loginError && <p className="error-message">{loginError}</p>}
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
                <button onClick={handleLogin}>Login</button>
            </div>
        );
    };

    const renderPage = () => {
        switch (currentPage) {
            case 'dashboard':
                return renderDeviceList();
            default:
                return <div>Page not found</div>;
        }
    };

    if (!loginStatus) {
        return renderLoginPage();
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>IoT Controller</h1>
            </header>
            <main>
                {renderPage()}
            </main>
        </div>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

export default App;
