import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom/client';
import io from 'socket.io-client';
import './App.css';

function App() {
    const [userId, setUserId] = useState(localStorage.getItem('userId') || '');
    const [username, setUsername] = useState('');
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const [rooms, setRooms] = useState([]);
    const [currentRoom, setCurrentRoom] = useState('general');
    const [isLoggedIn, setIsLoggedIn] = useState(!!userId);
    const [loginError, setLoginError] = useState('');
    const socket = useRef(null);
    const messagesEndRef = useRef(null);


    useEffect(() => {
        if (isLoggedIn) {
            socket.current = io('http://localhost:5403'); // Backend port
            socket.current.on('connect', () => {
                console.log('Connected to WebSocket');
            });

            socket.current.on('receive_message', (data) => {
                setMessages(prevMessages => [...prevMessages, data]);
            });

            socket.current.on('user_joined', (data) => {
                // Display a notification when a user joins the room
                setMessages(prevMessages => [...prevMessages, { content: `${data.user_id} joined the room.`, system: true }]);
            });

             // Join the default room upon successful login
             joinRoom(currentRoom);

            socket.current.on('disconnect', () => {
                console.log('Disconnected from WebSocket');
            });

            return () => {
                socket.current.disconnect();
            };
        }
    }, [isLoggedIn, currentRoom]);

    useEffect(() => {
        const fetchRooms = async () => {
            try {
                const response = await fetch('/api/rooms');
                if (!response.ok) {
                    throw new Error('Failed to fetch rooms');
                }
                const data = await response.json();
                setRooms(data);
            } catch (error) {
                console.error("Error fetching rooms:", error);
                // Optionally set an error state to display to the user
            }
        };

        fetchRooms();
    }, []);


    useEffect(() => {
        if (isLoggedIn) {
            fetchMessages(currentRoom);
        }
    }, [currentRoom, isLoggedIn]);

    const fetchMessages = async (roomId) => {
      try {
          const response = await fetch(`/api/messages/${roomId}`);
          if (!response.ok) {
              throw new Error('Failed to fetch messages');
          }
          const data = await response.json();
          setMessages(data);
      } catch (error) {
          console.error("Error fetching messages:", error);
          // Handle error appropriately (e.g., display an error message)
      }
  };


    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])


    const handleLogin = async (e) => {
        e.preventDefault();
        setLoginError('');

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                setLoginError(errorData.error || 'Login failed');
                return;
            }

            const data = await response.json();
            setUserId(data.user_id);
            localStorage.setItem('userId', data.user_id);
            setIsLoggedIn(true);
        } catch (error) {
            console.error('Login error:', error);
            setLoginError('Failed to connect to the server');
        }
    };

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (message && socket.current) {
            socket.current.emit('send_message', { user_id: userId, room_id: currentRoom, content: message });
            setMessage('');
        }
    };

    const joinRoom = (roomId) => {
        if (socket.current && userId) {
            socket.current.emit('join_room', { user_id: userId, room_id: roomId });
            setCurrentRoom(roomId);
            setMessages([]);  // Clear messages when joining a new room
        }
    };


    const handleLogout = () => {
        localStorage.removeItem('userId');
        setUserId('');
        setUsername('');
        setIsLoggedIn(false);
        socket.current.disconnect();

    };


    if (!isLoggedIn) {
        return (
            <div className="login-container">
                <h2>Login</h2>
                <form onSubmit={handleLogin}>
                    <input
                        type="text"
                        placeholder="Username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="login-input"
                    />
                    <button type="submit" className="login-button">Enter Chat</button>
                </form>
                {loginError && <p className="error-message">{loginError}</p>}
            </div>
        );
    }

    return (
        <div className="chat-container">
            <header className="chat-header">
                <h1>Chat Room</h1>
                <button className="logout-button" onClick={handleLogout}>Logout</button>
                <div>Logged in as: {username}</div>
            </header>

            <aside className="sidebar">
                <h2>Rooms</h2>
                <ul>
                    {rooms.map(room => (
                        <li key={room.id} className={currentRoom === room.id ? 'active' : ''} onClick={() => joinRoom(room.id)}>
                            {room.name}
                        </li>
                    ))}
                </ul>
            </aside>

            <main className="chat-main">
                <div className="message-container">
                    {messages.map((msg, index) => (
                         <div key={index} className={`message ${msg.user_id === userId ? 'sent' : 'received'} ${msg.system ? 'system-message' : ''}`}>
                            <div className="message-content">
                                {msg.system ? (
                                    <span className="system-text">{msg.content}</span>
                                ) : (
                                    <>
                                        <span className="message-author">{msg.username}:</span>
                                        <span className="message-text">{msg.content}</span>
                                    </>
                                )}
                                {!msg.system && <div className="message-timestamp">{msg.timestamp}</div>}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
                <form onSubmit={handleSendMessage} className="message-form">
                    <input
                        type="text"
                        placeholder="Enter your message..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        className="message-input"
                    />
                    <button type="submit" className="send-button">Send</button>
                </form>
            </main>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
