import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

function App() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [user_id, setUserId] = useState(null);
    const [room_id, setRoomId] = useState('');
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);
    const socket = io('http://localhost:5003');

    useEffect(() => {
        socket.on('joined_room', (data) => {
            console.log(`Joined room ${data.room_id}`);
        });

        socket.on('left_room', (data) => {
            console.log(`Left room ${data.room_id}`);
        });

        socket.on('new_message', (data) => {
            setMessages((prevMessages) => [...prevMessages, data.message]);
        });
    }, []);

    const handleLogin = () => {
        fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        })
            .then((response) => response.json())
            .then((data) => setUserId(data.user_id))
            .catch((error) => console.error(error));
    };

    const handleRegister = () => {
        fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        })
            .then((response) => response.json())
            .then((data) => setUserId(data.user_id))
            .catch((error) => console.error(error));
    };

    const handleJoinRoom = () => {
        socket.emit('join_room', { room_id, user_id });
    };

    const handleLeaveRoom = () => {
        socket.emit('leave_room', { room_id, user_id });
    };

    const handleSendMessage = () => {
        socket.emit('send_message', { room_id, message });
        setMessage('');
    };

    return (
        <div>
            {user_id ? (
                <div>
                    <h1>Welcome, {username}!</h1>
                    <input
                        type="text"
                        value={room_id}
                        onChange={(e) => setRoomId(e.target.value)}
                        placeholder="Room ID"
                    />
                    <button onClick={handleJoinRoom}>Join Room</button>
                    <button onClick={handleLeaveRoom}>Leave Room</button>
                    <input
                        type="text"
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        placeholder="Message"
                    />
                    <button onClick={handleSendMessage}>Send Message</button>
                    <ul>
                        {messages.map((message, index) => (
                            <li key={index}>{message}</li>
                        ))}
                    </ul>
                </div>
            ) : (
                <div>
                    <h1>Login or Register</h1>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Username"
                    />
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                    />
                    <button onClick={handleLogin}>Login</button>
                    <button onClick={handleRegister}>Register</button>
                </div>
            )}
        </div>
    );
}

export default App;
