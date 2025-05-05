import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import io from 'socket.io-client';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import './App.css';

const socket = io('http://localhost:5083');

const App = () => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState('');
  const [username, setUsername] = useState('');
  const [room, setRoom] = useState('');

  useEffect(() => {
    socket.on('message', (data) => {
      setMessages((prevMessages) => [...prevMessages, data]);
    });

    return () => {
      socket.off('message');
    };
  }, []);

  const sendMessage = () => {
    socket.emit('message', { username, message });
    setMessage('');
  };

  const joinRoom = () => {
    socket.emit('join', { username, room });
  };

  const leaveRoom = () => {
    socket.emit('leave', { username, room });
  };

  return (
    <Router>
      <div className="App">
        <Switch>
          <Route path="/login">
            <Login />
          </Route>
          <Route path="/register">
            <Register />
          </Route>
          <Route path="/chat">
            <Chat
              messages={messages}
              message={message}
              setMessage={setMessage}
              sendMessage={sendMessage}
              joinRoom={joinRoom}
              leaveRoom={leaveRoom}
              username={username}
              setUsername={setUsername}
              room={room}
              setRoom={setRoom}
            />
          </Route>
        </Switch>
      </div>
    </Router>
  );
};

const Login = () => {
  return <div>Login Component</div>;
};

const Register = () => {
  return <div>Register Component</div>;
};

const Chat = ({
  messages,
  message,
  setMessage,
  sendMessage,
  joinRoom,
  leaveRoom,
  username,
  setUsername,
  room,
  setRoom,
}) => {
  return (
    <div>
      <div>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="text"
          placeholder="Room"
          value={room}
          onChange={(e) => setRoom(e.target.value)}
        />
        <button onClick={joinRoom}>Join Room</button>
        <button onClick={leaveRoom}>Leave Room</button>
      </div>
      <div>
        {messages.map((msg, index) => (
          <div key={index}>{msg.username}: {msg.message}</div>
        ))}
      </div>
      <div>
        <input
          type="text"
          placeholder="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
