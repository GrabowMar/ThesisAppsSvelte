import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [route, setRoute] = useState('login'); // Initial route
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [currentUsername, setCurrentUsername] = useState(null);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const response = await fetch('/api/check_auth');
            const data = await response.json();
            if (data.username) {
                setIsLoggedIn(true);
                setCurrentUsername(data.username);
                setRoute('dashboard');
            } else {
                setIsLoggedIn(false);
                setCurrentUsername(null);
                setRoute('login');
            }
        } catch (error) {
            console.error("Error checking authentication:", error);
            setMessage("Failed to check authentication.");
        }
    };


    const handleRegister = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            setMessage(data.message);

            if (response.status === 201) {
                setRoute('login');
            }
        } catch (error) {
            console.error("Registration error:", error);
            setMessage("Registration failed.");
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();
            setMessage(data.message);

            if (response.status === 200) {
                setIsLoggedIn(true);
                setCurrentUsername(username);
                setRoute('dashboard');
            }
        } catch (error) {
            console.error("Login error:", error);
            setMessage("Login failed.");
        }
    };

    const handleLogout = async () => {
        try {
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            setMessage(data.message);
            setIsLoggedIn(false);
            setCurrentUsername(null);
            setRoute('login');
        } catch (error) {
            console.error("Logout error:", error);
            setMessage("Logout failed.");
        }
    };

    let content;

    if (route === 'register') {
        content = (
            <div className="auth-container">
                <h2>Register</h2>
                {message && <p className="message">{message}</p>}
                <form onSubmit={handleRegister}>
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
                    <button type="submit">Register</button>
                    <button type="button" onClick={() => setRoute('login')}>
                        Already have an account? Login
                    </button>
                </form>
            </div>
        );
    } else if (route === 'login') {
        content = (
            <div className="auth-container">
                <h2>Login</h2>
                {message && <p className="message">{message}</p>}
                <form onSubmit={handleLogin}>
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
                    <button type="submit">Login</button>
                    <button type="button" onClick={() => setRoute('register')}>
                        Need an account? Register
                    </button>
                </form>
            </div>
        );
    } else if (route === 'dashboard') {
        content = (
            <div className="dashboard-container">
                <h2>Dashboard</h2>
                {message && <p className="message">{message}</p>}
                <p>Welcome, {currentUsername}!</p>
                <button onClick={handleLogout}>Logout</button>
            </div>
        );
    } else {
        content = <p>Page not found</p>;
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>Authentication System</h1>
            </header>
            {content}
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
