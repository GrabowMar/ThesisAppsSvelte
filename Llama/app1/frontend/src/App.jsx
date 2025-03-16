import React, { useState, useEffect } from 'react';
import './App.css';
import { io } from 'socket.io-client';

const socket = io('http://localhost:5003');

function App() {
    const [username, setUsername] = useState('');
    const [message, setMessage] = useState('');
    const [chatMessages, setChatMessages] = useState([]);
    const [onlineUsers, setOnlineUsers] = useState({});

    useEffect(() => {
        // Fetch initial online users and chat messages
        fetch('http://localhost:5003/dashboard')
            .then(response => response.json())
            .then(data => console.log(data));

        // Listen for incoming messages
        socket.on('receive_message', (data) => {
            setChatMessages((prevMessages) => [...prevMessages, data]);
        });

        // Listen for updates to online status
        socket.on('update_online_status', (data) => {
            setOnlineUsers((prevUsers) => ({ ...prevUsers, [data.username]: data.status }));
        });
    }, []);

    const handleLogin = () => {
        // Send login request to backend
        fetch('http://localhost:5003/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username }),
        })
            .then(response => response.json())
            .then(data => console.log(data));

        // Update online status
        socket.emit('update_online_status', { username, status: true });
    };

    const handleRegister = () => {
        // Send register request to backend
        fetch('http://localhost:5003/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username }),
        })
            .then(response => response.json())
            .then(data => console.log(data));
    };

    const handleSendMessage = () => {
        // Send message to backend
        socket.emit('send_message', { username, message });

        // Clear message input
        setMessage('');
    };

    return (
        <div className="App">
            <h1>Chat Application</h1>
            <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
            <button onClick={handleLogin}>Login</button>
            <button onClick={handleRegister}>Register</button>
            <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Message" />
            <button onClick={handleSendMessage}>Send Message</button>
            <ul>
                {chatMessages.map((message, index) => (
                    <li key={index}>{message.username}: {message.message}</li>
                ))}
            </ul>
            <h2>Online Users:</h2>
            <ul>
                {Object.keys(onlineUsers).map((username, index) => (
                    <li key={index}>{username}: {onlineUsers[username] ? 'Online' : 'Offline'}</li>
                ))}
            </ul>
        </div>
    );
}

export default App;