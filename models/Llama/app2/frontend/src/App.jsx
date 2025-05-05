import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';

function App() {
  const [username, setUsername] = useState('');
  const [onlineStatus, setOnlineStatus] = useState(false);
  const [chatRoom, setChatRoom] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    axios.get('/api/get_chat_rooms')
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleLogin = () => {
    axios.post('/api/login', { username: username })
      .then(response => {
        console.log(response.data);
        setOnlineStatus(true);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleLogout = () => {
    axios.post('/api/logout', { username: username })
      .then(response => {
        console.log(response.data);
        setOnlineStatus(false);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleSendMessage = () => {
    axios.post('/api/send_message', { sender_username: username, receiver_username: chatRoom, message: message })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleGetMessages = () => {
    axios.post('/api/get_messages', { sender_username: username, receiver_username: chatRoom })
      .then(response => {
        console.log(response.data);
        setMessages(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleCreateChatRoom = () => {
    axios.post('/api/create_chat_room', { room_name: chatRoom })
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <h1>Chat Application</h1>
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" />
      <button onClick={handleLogin}>Login</button>
      <button onClick={handleLogout}>Logout</button>
      <input type="text" value={chatRoom} onChange={(e) => setChatRoom(e.target.value)} placeholder="Chat Room" />
      <input type="text" value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Message" />
      <button onClick={handleSendMessage}>Send Message</button>
      <button onClick={handleGetMessages}>Get Messages</button>
      <button onClick={handleCreateChatRoom}>Create Chat Room</button>
      <ul>
        {messages.map((message, index) => (
          <li key={index}>{message.sender_username}: {message.message}</li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
