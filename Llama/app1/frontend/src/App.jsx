import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import { io } from 'socket.io-client';

const socket = io('http://localhost:5003');

function App() {
  const [username, setUsername] = useState('');
  const [message, setMessage] = useState('');
  const [room, setRoom] = useState('');
  const [messages, setMessages] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState([]);

  useEffect(() => {
    socket.on('receive_message', (data) => {
      setMessages((prevMessages) => [...prevMessages, data]);
    });

    socket.on('connect', () => {
      console.log('Connected to the server');
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from the server');
    });
  }, []);

  const handleSendMessage = () => {
    socket.emit('send_message', { username, message, room });
    setMessage('');
  };

  const handleGetMessages = () => {
    fetch('http://localhost:5003/get_messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room }),
    })
      .then((response) => response.json())
      .then((data) => setMessages(data.messages));
  };

  const handleGetOnlineUsers = () => {
    fetch('http://localhost:5003/get_online_users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room }),
    })
      .then((response) => response.json())
      .then((data) => setOnlineUsers(data.online_users));
  };

  const handleRegister = () => {
    fetch('http://localhost:5003/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data));
  };

  const handleLogin = () => {
    fetch('http://localhost:5003/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data));
  };

  const handleLogout = () => {
    fetch('http://localhost:5003/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data));
  };

  return (
    <div className="app">
      <h1>Chat Application</h1>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
      />
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Message"
      />
      <input
        type="text"
        value={room}
        onChange={(e) => setRoom(e.target.value)}
        placeholder="Room"
      />
      <button onClick={handleSendMessage}>Send Message</button>
      <button onClick={handleGetMessages}>Get Messages</button>
      <button onClick={handleGetOnlineUsers}>Get Online Users</button>
      <button onClick={handleRegister}>Register</button>
      <button onClick={handleLogin}>Login</button>
      <button onClick={handleLogout}>Logout</button>
      <h2>Messages:</h2>
      <ul>
        {messages.map((message, index) => (
          <li key={index}>{message.username}: {message.message}</li>
        ))}
      </ul>
      <h2>Online Users:</h2>
      <ul>
        {onlineUsers.map((user, index) => (
          <li key={index}>{user}</li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root')