// App.jsx

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { io } from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:5483');

const App = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [currentRoom, setCurrentRoom] = useState('general');
  const [rooms, setRooms] = useState([]);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    socket.on('message', (data) => {
      if (data.room === currentRoom) {
        setMessages(prevMessages => [...prevMessages, data]);
      }
    });
    socket.on('status', (data) => {
      if (data.room === currentRoom) {
        setMessages(prevMessages => [...prevMessages, { username: 'System', message: data.msg }]);
      }
    });
    return () => {
      socket.off('message');
      socket.off('status');
    };
  }, [currentRoom]);

  const handleRegister = async () => {
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (response.ok) {
        alert('Registration successful');
      } else {
        const errorData = await response.json();
        setError(errorData.error);
      }
    } catch (error) {
      setError('An error occurred during registration');
    }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (response.ok) {
        setLoggedIn(true);
        setError('');
        setUsername('');
        setPassword('');
        fetchRooms();
      } else {
        const errorData = await response.json();
        setError(errorData.error);
      }
    } catch (error) {
      setError('An error occurred during login');
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/logout', {
        method: 'POST'
      });
      if (response.ok) {
        setLoggedIn(false);
        setCurrentRoom('general');
        setMessages([]);
        setRooms([]);
      }
    } catch (error) {
      setError('An error occurred during logout');
    }
  };

  const fetchRooms = async () => {
    try {
      const response = await fetch('/api/rooms');
      if (response.ok) {
        const data = await response.json();
        setRooms(data);
      }
    } catch (error) {
      setError('An error occurred while fetching rooms');
    }
  };

  const fetchMessages = async (room) => {
    try {
      const response = await fetch(`/api/room/${room}/messages`);
      if (response.ok) {
        const data = await response.json();
        setMessages(data);
      }
    } catch (error) {
      setError('An error occurred while fetching messages');
    }
  };

  const handleJoinRoom = async (room) => {
    try {
      const response = await fetch(`/api/room/${room}/join`, {
        method: 'POST'
      });
      if (response.ok) {
        setCurrentRoom(room);
        fetchMessages(room);
        socket.emit('join', { room });
      }
    } catch (error) {
      setError('An error occurred while joining the room');
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
      socket.emit('message', { room: currentRoom, message: newMessage });
      setNewMessage('');
    }
  };

  if (!loggedIn) {
    return (
      <div className="login-container">
        <h1>Chat Application</h1>
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
        <button onClick={handleRegister}>Register</button>
        <button onClick={handleLogin}>Login</button>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="sidebar">
        <h2>Rooms</h2>
        <ul>
          {rooms.map(room => (
            <li key={room} onClick={() => handleJoinRoom(room)}>
              {room}
            </li>
          ))}
        </ul>
        <button onClick={handleLogout}>Logout</button>
      </div>
      <div className="main">
        <h2>{currentRoom}</h2>
        <div className="message-list">
          {messages.map((msg, index) => (
            <div key={index} className="message">
              <strong>{msg.username}: </strong> {msg.message}
            </div>
          ))}
        </div>
        <form onSubmit={handleSendMessage}>
          <input
            type="text"
            placeholder="Type a message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
