// 1. Imports
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Link, Switch } from 'react-router-dom';
import axios from 'axios';

// 2. State Management
const [username, setUsername] = useState('');
const [password, setPassword] = useState('');
const [isLoggedIn, setIsLoggedIn] = useState(false);
const [error, setError] = useState(null);

// 3. Lifecycle Functions
useEffect(() => {
    if (localStorage.getItem('username')) {
        setIsLoggedIn(true);
    }
}, []);

// 4. Event Handlers
const handleRegister = async (event) => {
    event.preventDefault();
    try {
        const response = await axios.post('http://localhost:5001/register', {
            username,
            password,
        });
        if (response.status === 201) {
            setIsLoggedIn(true);
            localStorage.setItem('username', username);
        }
    } catch (error) {
        setError(error.response.data.message);
    }
};

const handleLogin = async (event) => {
    event.preventDefault();
    try {
        const response = await axios.post('http://localhost:5001/login', {
            username,
            password,
        });
        if (response.status === 200) {
            setIsLoggedIn(true);
            localStorage.setItem('username', username);
        }
    } catch (error) {
        setError(error.response.data.message);
    }
};

const handleLogout = async () => {
    try {
        const response = await axios.post('http://localhost:5001/logout');
        if (response.status === 200) {
            setIsLoggedIn(false);
            localStorage.removeItem('username');
        }
    } catch (error) {
        setError(error.response.data.message);
    }
};

// 5. API Calls
const getDashboard = async () => {
    try {
        const response = await axios.get('http://localhost:5001/dashboard');
        if (response.status === 200) {
            return response.data.message;
        }
    } catch (error) {
        setError(error.response.data.message);
    }
};

// 6. Render
return (
    <Router>
        <div>
            <nav>
                <ul>
                    <li>
                        <Link to="/">Register</Link>
                    </li>
                    <li>
                        <Link to="/login">Login</Link>
                    </li>
                    {isLoggedIn && (
                        <li>
                            <Link to="/dashboard">Dashboard</Link>
                        </li>
                    )}
                    {isLoggedIn && (
                        <li>
                            <button onClick={handleLogout}>Logout</button>
                        </li>
                    )}
                </ul>
            </nav>
            <Switch>
                <Route exact path="/">
                    <form onSubmit={handleRegister}>
                        <label>
                            Username:
                            <input type="text" value={username} onChange={(event) => setUsername(event.target.value)} />
                        </label>
                        <br />
                        <label>
                            Password:
                            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                        </label>
                        <br />
                        <button type="submit">Register</button>
                    </form>
                </Route>
                <Route exact path="/login">
                    <form onSubmit={handleLogin}>
                        <label>
                            Username:
                            <input type="text" value={username} onChange={(event) => setUsername(event.target.value)} />
                        </label>
                        <br />
                        <label>
                            Password:
                            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
                        </label>
                        <br />
                        <button type="submit">Login</button>
                    </form>
                </Route>
                <Route exact path="/dashboard">
                    {isLoggedIn ? (
                        <div>
                            <h1>Welcome to the dashboard!</h1>
                            <p>{getDashboard()}</p>
                        </div>
                    ) : (
                        <div>
                            <h1>You are not logged in.</h1>
                        </div>
                    )}
                </Route>
            </Switch>
            {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
    </Router>
);
