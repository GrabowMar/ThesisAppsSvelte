import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, useNavigate } from 'react-router-dom';
import io from 'socket.io-client';
import axios from 'axios';
import './App.css';

const socket = io('http://localhost:5083');

const Login = ({ setUsername }) => {
  const [username, setLocalUsername] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      await axios.post('http://localhost:5083/login', { username });
      setUsername(username);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setLocalUsername(e.target.value)}
      />
      <button onClick={handleLogin}>Login</button>
    </div>
  );
};

const Register = ({ setUsername }) => {
  const [username, setLocalUsername] = useState('');
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await axios.post('http://localhost:5083/register', { username });
      setUsername(username);
      navigate('/dashboard');
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setLocalUsername(e.target.value)}
      />
      <button onClick={handleRegister}>Register</button>
    </div>
  );
};

const Dashboard = ({ username }) => {
  const [room, setRoom] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState(new Set());

  useEffect(() => {
    socket.on('user_connected', (data) => {
      setOnlineUsers((prevUsers) => new Set(prevUsers.add(data.username)));
    });

    socket.on('user_disconnected', (data) => {
      setOnlineUsers((prevUsers) => {
        const newSet = new Set(prevUsers);
        newSet.delete(data.username);
        return newSet;
      });
    });

    socket.on('new_message', (data) => {
      setMessages((prevMessages) => [...prevMessages, data]);
    });

    return () => {
      socket.off('user_connected');
      socket.off('user_disconnected');
      socket.off('new_message');
    };
  }, []);

  const handleJoinRoom = () => {
    socket.emit('join_room', { room });
    setRoom('');
  };

  const handleLeaveRoom = () => {
    socket.emit('leave_room', { room });
  };

  const handleSendMessage = () => {
    socket.emit('send_message', { room, message });
    setMessage('');
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {username}!</p>
      <div>
        <h3>Online Users</h3>
        <ul>
          {Array.from(onlineUsers).map((user) => (
            <li key={user}>{user}</li>
          ))}
        </ul>
      </div>
      <div>
        <input
          type="text"
          placeholder="Room"
          value={room}
          onChange={(e) => setRoom(e.target.value)}
        />
        <button onClick={handleJoinRoom}>Join Room</button>
        <button onClick={handleLeaveRoom}>Leave Room</button>
      </div>
      <div>
        <input
          type="text"
          placeholder="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button onClick={handleSendMessage}>Send Message</button>
      </div>
      <div>
        <h3>Messages</h3>
        <ul>
          {messages.map((msg, index) => (
            <li key={index}>{`${msg.username}: ${msg.message}`}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

const App = () => {
  const [username, setUsername] = useState(null);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login setUsername={setUsername} />} />
        <Route path="/register" element={<Register setUsername={setUsername} />} />
        <Route path="/dashboard" element={<Dashboard username={username} />} />
      </Routes>
    </Router>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
