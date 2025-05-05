// app/frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

// Define the backend URL (adjust if running behind a proxy)
const BACKEND_URL = 'http://localhost:6143';

const App = () => {
  // Application state: page can be 'login', 'register', or 'chat'
  const [page, setPage] = useState('login');
  const [username, setUsername] = useState('');
  const [room, setRoom] = useState('General');
  const [error, setError] = useState('');
  const [socket, setSocket] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [message, setMessage] = useState('');
  const [status, setStatus] = useState('');

  // Handle mounting the SocketIO connection when switching to chat page.
  useEffect(() => {
    if (page === 'chat' && !socket) {
      const newSocket = io(BACKEND_URL);
      setSocket(newSocket);

      newSocket.on('connect', () => {
        console.log('Connected to chat server');
        newSocket.emit('join', { username, room });
      });

      newSocket.on('connection_accepted', (data) => {
        console.log(data.message);
      });

      newSocket.on('chat_history', (data) => {
        setChatHistory(data.messages);
      });

      newSocket.on('message', (data) => {
        setChatHistory(prev => [...prev, data]);
      });

      newSocket.on('status', (data) => {
        setStatus(data.message);
        setTimeout(() => setStatus(''), 3000);
      });

      newSocket.on('error', (data) => {
        setError(data.error);
        setTimeout(() => setError(''), 3000);
      });

      return () => newSocket.disconnect();
    }
  }, [page, socket, username, room]);

  // Handle login form submission (dummy).
  const handleLogin = (e) => {
    e.preventDefault();
    if (!username) {
      setError('Username is required.');
      return;
    }
    // Here you can call the backend /login API.
    fetch(`${BACKEND_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: 'dummy' })
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setPage('chat');
        }
      })
      .catch(err => {
        setError('Login failed. Please try again.');
      });
  };

  // Handle register form submission (dummy).
  const handleRegister = (e) => {
    e.preventDefault();
    if (!username) {
      setError('Username is required.');
      return;
    }
    // Here you can call the backend /register API.
    fetch(`${BACKEND_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: 'dummy' })
    })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setPage('chat');
        }
      })
      .catch(err => {
        setError('Registration failed. Please try again.');
      });
  };

  // Handle sending a chat message via socket.
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    if (socket) {
      socket.emit('message', { username, room, message });
      setMessage('');
    }
  };

  // Render different pages based on the "page" state.
  return (
    <div className="container">
      {page === 'login' && (
        <div className="auth-container">
          <h2>Login</h2>
          <form onSubmit={handleLogin}>
            <input
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
            <button type="submit">Login</button>
          </form>
          <p>
            Don't have an account?{' '}
            <span className="link" onClick={() => setPage('register')}>
              Register here.
            </span>
          </p>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      {page === 'register' && (
        <div className="auth-container">
          <h2>Register</h2>
          <form onSubmit={handleRegister}>
            <input
              type="text"
              placeholder="Enter username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
            <button type="submit">Register</button>
          </form>
          <p>
            Already have an account?{' '}
            <span className="link" onClick={() => setPage('login')}>
              Login here.
            </span>
          </p>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      {page === 'chat' && (
        <div className="chat-container">
          <header className="chat-header">
            <h2>Chat Room: {room}</h2>
            <span className="status">{status}</span>
          </header>
          <section className="chat-history">
            {chatHistory.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.username === username ? 'own' : ''}`}>
                <strong>{msg.username}: </strong>
                <span>{msg.message}</span>
              </div>
            ))}
          </section>
          <form className="chat-input" onSubmit={handleSendMessage}>
            <input
              type="text"
              placeholder="Type a message..."
              value={message}
              onChange={e => setMessage(e.target.value)}
              required
            />
            <button type="submit">Send</button>
          </form>
          {error && <div className="error">{error}</div>}
        </div>
      )}
    </div>
  );
};

// Mount the App component to the DOM element with id "root"
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);

export default App;
