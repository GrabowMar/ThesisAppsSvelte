import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

// API Base URL
const API_URL = 'http://localhost:5323/api';

// Socket.io client setup
const socket = io('http://localhost:5323');

// Root App Component
function App() {
  const [view, setView] = useState('login'); // login, register, chat
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check if user is authenticated
  useEffect(() => {
    if (token) {
      // Validate token on load
      fetch(`${API_URL}/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(response => {
        if (response.ok) {
          setView('chat');
        } else {
          // Token invalid, log user out
          handleLogout();
        }
      })
      .catch(err => {
        console.error('Error validating token:', err);
        handleLogout();
      });
    }
  }, [token]);

  // Handle logout
  const handleLogout = async () => {
    try {
      if (token) {
        await fetch(`${API_URL}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage and state
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setToken('');
      setUser(null);
      setView('login');
    }
  };

  // Show different views based on state
  return (
    <div className="app-container">
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      {view === 'login' && (
        <LoginForm 
          setView={setView} 
          setToken={setToken} 
          setUser={setUser}
          setError={setError}
          setSuccess={setSuccess}
        />
      )}
      
      {view === 'register' && (
        <RegisterForm 
          setView={setView}
          setToken={setToken}
          setUser={setUser}
          setError={setError}
          setSuccess={setSuccess}
        />
      )}
      
      {view === 'chat' && user && (
        <ChatInterface 
          token={token} 
          user={user}
          handleLogout={handleLogout}
          setError={setError}
        />
      )}
    </div>
  );
}

// Login Component
function LoginForm({ setView, setToken, setUser, setError, setSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Login failed');
      }
      
      // Success - store token and user data
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      setToken(data.token);
      setUser(data.user);
      setSuccess('Login successful!');
      setView('chat');
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Chat App Login</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input 
            type="text" 
            id="username" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            placeholder="Your username"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            placeholder="Your password"
          />
        </div>
        
        <button 
          type="submit" 
          className="auth-button"
          disabled={isLoading}
        >
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      
      <p className="auth-switch">
        Don't have an account?{' '}
        <button 
          onClick={() => setView('register')}
          disabled={isLoading}
        >
          Register
        </button>
      </p>
    </div>
  );
}

// Register Component
function RegisterForm({ setView, setToken, setUser, setError, setSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Registration failed');
      }
      
      // Success - store token and user data
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      setToken(data.token);
      setUser(data.user);
      setSuccess('Registration successful!');
      setView('chat');
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <h1>Create an Account</h1>
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input 
            type="text" 
            id="username" 
            value={username} 
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            placeholder="Choose a username"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input 
            type="password" 
            id="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            placeholder="Create a password"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirm Password</label>
          <input 
            type="password" 
            id="confirmPassword" 
            value={confirmPassword} 
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={isLoading}
            placeholder="Confirm your password"
          />
        </div>
        
        <button 
          type="submit" 
          className="auth-button"
          disabled={isLoading}
        >
          {isLoading ? 'Registering...' : 'Register'}
        </button>
      </form>
      
      <p className="auth-switch">
        Already have an account?{' '}
        <button 
          onClick={() => setView('login')}
          disabled={isLoading}
        >
          Login
        </button>
      </p>
    </div>
  );
}

// Main Chat Interface Component
function ChatInterface({ token, user, handleLogout, setError }) {
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [users, setUsers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isCreatingRoom, setIsCreatingRoom] = useState(false);
  const [newRoomName, setNewRoomName] = useState('');
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef(null);

  // Load initial data - rooms and users
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch rooms
        const roomsResponse = await fetch(`${API_URL}/rooms`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!roomsResponse.ok) {
          throw new Error('Failed to fetch rooms');
        }
        
        const roomsData = await roomsResponse.json();
        setRooms(roomsData.rooms);
        
        // If rooms exist, select the General room or the first room by default
        if (roomsData.rooms.length > 0) {
          const generalRoom = roomsData.rooms.find(room => room.name === 'General');
          setSelectedRoom(generalRoom || roomsData.rooms[0]);
        }
        
        // Fetch users
        const usersResponse = await fetch(`${API_URL}/users`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (!usersResponse.ok) {
          throw new Error('Failed to fetch users');
        }
        
        const usersData = await usersResponse.json();
        setUsers(usersData.users);
        
      } catch (error) {
        console.error('Error fetching initial data:', error);
        setError('Failed to load chat data. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchInitialData();
  }, [token, setError]);

  // Load messages when room is selected
  useEffect(() => {
    if (selectedRoom) {
      fetchRoomMessages(selectedRoom.id);
      
      // Join the room through socket.io
      socket.emit('join', {
        room: selectedRoom.name,
        username: user.username,
        user_id: user.id
      });
      
      // Cleanup function to leave room when component unmounts or room changes
      return () => {
        socket.emit('leave', {
          room: selectedRoom.name,
          username: user.username
        });
      };
    }
  }, [selectedRoom, user]);

  // Set up socket.io event listeners
  useEffect(() => {
    // Listen for new messages
    socket.on('message', (message) => {
      if (selectedRoom && message.room === selectedRoom.name) {
        setMessages((prevMessages) => [...prevMessages, message]);
      }
    });
    
    // Listen for user status updates
    socket.on('user_status', (userData) => {
      setUsers((prevUsers) => 
        prevUsers.map(u => 
          u.id === userData.user_id ? { ...u, online: userData.online } : u
        )
      );
    });
    
    // Listen for errors
    socket.on('error', (err) => {
      setError(err.message);
    });
    
    // Cleanup listeners on component unmount
    return () => {
      socket.off('message');
      socket.off('user_status');
      socket.off('error');
    };
  }, [selectedRoom, setError]);

  // Scroll to bottom of messages when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Fetch messages for a specific room
  const fetchRoomMessages = async (roomId) => {
    try {
      const response = await fetch(`${API_URL}/rooms/${roomId}/messages`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }
      
      const data = await response.json();
      setMessages(data.messages);
    } catch (error) {
      console.error('Error fetching messages:', error);
      setError('Failed to load messages. Please try again.');
    }
  };

  // Send a new message
  const sendMessage = (e) => {
    e.preventDefault();
    
    if (!messageInput.trim() || !selectedRoom) return;
    
    socket.emit('message', {
      room: selectedRoom.name,
      user_id: user.id,
      message: messageInput
    });
    
    setMessageInput('');
  };

  // Create a new room
  const createRoom = async (e) => {
    e.preventDefault();
    
    if (!newRoomName.trim()) {
      setError('Room name is required');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: newRoomName }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.message || 'Failed to create room');
      }
      
      // Add new room to list and select it
      setRooms([...rooms, data.room]);
      setSelectedRoom(data.room);
      
      // Reset form
      setNewRoomName('');
      setIsCreatingRoom(false);
    } catch (error) {
      setError(error.message);
    }
  };

  // Loading state
  if (loading) {
    return <div className="loading">Loading chat...</div>;
  }

  return (
    <div className="chat-container">
      {/* Sidebar with rooms and users */}
      <div className="chat-sidebar">
        <div className="user-profile">
          <h3>Welcome, {user.username}</h3>
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
        
        {/* Rooms section */}
        <div className="rooms-section">
          <div className="section-header">
            <h3>Rooms</h3>
            <button 
              className="create-room-button"
              onClick={() => setIsCreatingRoom(!isCreatingRoom)}
            >
              {isCreatingRoom ? 'Cancel' : '+ New Room'}
            </button>
          </div>
          
          {/* Create room form */}
          {isCreatingRoom && (
            <form className="create-room-form" onSubmit={createRoom}>
              <input
                type="text"
                value={newRoomName}
                onChange={(e) => setNewRoomName(e.target.value)}
                placeholder="Room name"
                required
              />
              <button type="submit">Create</button>
            </form>
          )}
          
          {/* Room list */}
          <ul className="room-list">
            {rooms.map((room) => (
              <li 
                key={room.id} 
                className={selectedRoom && selectedRoom.id === room.id ? 'active' : ''}
                onClick={() => setSelectedRoom(room)}
              >
                # {room.name}
              </li>
            ))}
          </ul>
        </div>
        
        {/* Users section */}
        <div className="users-section">
          <h3>Users</h3>
          <ul className="user-list">
            {users.map((u) => (
              <li key={u.id} className={u.online ? 'online' : 'offline'}>
                <span className="status-indicator"></span>
                {u.username}
                {u.id === user.id && ' (you)'}
              </li>
            ))}
          </ul>
        </div>
      </div>
      
      {/* Main chat area */}
      <div className="chat-main">
        {selectedRoom ? (
          <>
            <div className="chat-header">
              <h2>#{selectedRoom.name}</h2>
            </div>
            
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="empty-messages">
                  No messages yet. Be the first to say something!
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div 
                    key={msg.id || index} 
                    className={`message ${msg.user_id === user.id ? 'own-message' : ''} ${msg.user === 'system' ? 'system-message' : ''}`}
                  >
                    {msg.user !== 'system' && (
                      <div className="message-user">{msg.user}</div>
                    )}
                    <div className="message-content">{msg.content}</div>
                    <div className="message-time">
                      {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <form className="message-form" onSubmit={sendMessage}>
              <input
                type="text"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                placeholder="Type a message..."
                className="message-input"
              />
              <button type="submit" className="send-button">Send</button>
            </form>
          </>
        ) : (
          <div className="no-room-selected">
            <h2>Welcome to the Chat App</h2>
            <p>Select a room to start chatting</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Mount the React app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;

