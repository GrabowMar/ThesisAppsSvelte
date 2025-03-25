// Import required dependencies and initialize React
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
    // State to manage client-side routing
    const [route, setRoute] = useState('login'); // Possible routes: 'login', 'register', 'dashboard'
    const [user, setUser] = useState(null); // Store logged-in user data
    const [error, setError] = useState(''); // Store error messages

    // API base URL
    const API_BASE_URL = 'http://localhost:5241';

    // Helper: Make API calls
    const apiCall = async (endpoint, method, body = null) => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: method,
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json' 
                },
                body: body ? JSON.stringify(body) : undefined,
                credentials: 'include', // Include cookies for session management
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            return data;
        } catch (err) {
            setError(err.message);
            return null;
        }
    };

    // Handle Login
    const handleLogin = async (e) => {
        e.preventDefault();
        const username = e.target.username.value.trim();
        const password = e.target.password.value;

        const result = await apiCall('/login', 'POST', { username, password });
        if (result) {
            setUser(result.user);
            setRoute('dashboard');
        }
    };

    // Handle Register
    const handleRegister = async (e) => {
        e.preventDefault();
        const username = e.target.username.value.trim();
        const password = e.target.password.value;

        const result = await apiCall('/register', 'POST', { username, password });
        if (result) setRoute('login');
    };

    // Handle Logout
    const handleLogout = async () => {
        const result = await apiCall('/logout', 'POST');
        if (result) {
            setUser(null);
            setRoute('login');
        }
    };

    // Fetch dashboard data on loading the dashboard
    useEffect(() => {
        const fetchDashboard = async () => {
            if (route === 'dashboard') {
                const data = await apiCall('/dashboard', 'GET');
                if (data) setUser(data.user);
            }
        };
        fetchDashboard();
    }, [route]);

    // Render Routes
    const renderRoute = () => {
        switch (route) {
            case 'login':
                return (
                    <div className="auth-container">
                        <h2>Login</h2>
                        <form onSubmit={handleLogin}>
                            <input type="text" name="username" placeholder="Username" required />
                            <input type="password" name="password" placeholder="Password" required />
                            <button type="submit">Login</button>
                        </form>
                        <p>
                            Don't have an account?{' '}
                            <span onClick={() => setRoute('register')} className="link">
                                Register
                            </span>
                        </p>
                    </div>
                );
            case 'register':
                return (
                    <div className="auth-container">
                        <h2>Register</h2>
                        <form onSubmit={handleRegister}>
                            <input type="text" name="username" placeholder="Username" required />
                            <input type="password" name="password" placeholder="Password" required />
                            <button type="submit">Register</button>
                        </form>
                        <p>
                            Already have an account?{' '}
                            <span onClick={() => setRoute('login')} className="link">
                                Login
                            </span>
                        </p>
                    </div>
                );
            case 'dashboard':
                return (
                    <div className="dashboard">
                        <h2>Welcome, {user?.username}!</h2>
                        <button onClick={handleLogout}>Logout</button>
                    </div>
                );
            default:
                return <p>Page not found</p>;
        }
    };

    return (
        <div className="app-container">
            <h1>Flask + React Auth App</h1>
            {error && <div className="error-message">{error}</div>}
            {renderRoute()}
        </div>
    );
};

// Mount React application to the DOM
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
