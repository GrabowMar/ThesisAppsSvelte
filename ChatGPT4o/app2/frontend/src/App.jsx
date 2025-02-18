import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:5003');

const App = () => {
    const [username, setUsername] = useState('');
    const [room, setRoom] = useState('general');
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        socket.on('message', (data) => {
            setMessages((prev) => [...prev, data]);
        });
    }, []);

    const handleLogin = async () => {
        if (!username) return;
        setIsLoggedIn(true);
        socket.emit('join', { username, room });
    };

    const handleSendMessage = () => {
        if (message) {
            socket.emit('message', { username, room, message });
            setMessage('');
        }
    };

    return (
        <div className="chat-container">
            {!isLoggedIn ? (
                <div className="login-container">
                    <input type="text" placeholder="Enter username" value={username} onChange={(e) => setUsername(e.target.value)} />
                    <button onClick={handleLogin}>Join Chat</button>
                </div>
            ) : (
                <div className="chat-room">
                    <h2>Room: {room}</h2>
                    <div className="messages">
                        {messages.map((msg, index) => (
                            <div key={index}><strong>{msg.username}:</strong> {msg.message}</div>
                        ))}
                    </div>
                    <input type="text" placeholder="Type a message..." value={message} onChange={(e) => setMessage(e.target.value)} />
                    <button onClick={handleSendMessage}>Send</button>
                </div>
            )}
        </div>
    );
};

const root = createRoot(document.getElementById('root'));
root.render(<App />);