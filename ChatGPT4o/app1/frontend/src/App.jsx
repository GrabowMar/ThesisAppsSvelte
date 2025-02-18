import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const API_URL = 'http://localhost:5001';

function App() {
    const [page, setPage] = useState('login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [user, setUser] = useState(null);

    useEffect(() => {
        checkSession();
    }, []);

    const checkSession = async () => {
        try {
            const response = await fetch(`${API_URL}/dashboard`, { credentials: 'include' });
            const data = await response.json();
            if (response.ok) setUser(data.message);
        } catch (error) {
            console.error('Error checking session', error);
        }
    };

    const handleSubmit = async (e, endpoint) => {
        e.preventDefault();
        setMessage('');
        try {
            const response = await fetch(`${API_URL}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ username, password }),
            });
            const data = await response.json();
            if (response.ok) {
                if (endpoint === 'login') setUser(data.user);
                setMessage(data.message);
            } else {
                setMessage(data.message);
            }
        } catch (error) {
            setMessage('Server error');
        }
    };

    const handleLogout = async () => {
        try {
            await fetch(`${API_URL}/logout`, { method: 'POST', credentials: 'include' });
            setUser(null);
        } catch (error) {
            console.error('Logout failed', error);
        }
    };

    return (
        <div className="container">
            <h1>{user ? 'Dashboard' : 'Authentication'}</h1>
            {message && <p>{message}</p>}
            {user ? (
                <div>
                    <p>Welcome, {user}!</p>
                    <button onClick={handleLogout}>Logout</button>
                </div>
            ) : (
                <form onSubmit={(e) => handleSubmit(e, page)}>
                    <input type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
                    <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                    <button type="submit">{page === 'login' ? 'Login' : 'Register'}</button>
                </form>
            )}
            <button onClick={() => setPage(page === 'login' ? 'register' : 'login')}>
                {page === 'login' ? 'Go to Register' : 'Go to Login'}
            </button>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);