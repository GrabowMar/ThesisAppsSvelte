import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [user, setUser] = useState(null);
  const [room, setRoom] = useState("general");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);

  // Register user
  const registerUser = async (name) => {
    const response = await fetch("http://localhost:5163/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    const data = await response.json();
    setUser(data);
  };

  // Fetch messages
  const fetchMessages = async () => {
    const response = await fetch(`http://localhost:5163/messages/${room}`);
    const data = await response.json();
    setMessages(data);
  };

  // Fetch users
  const fetchUsers = async () => {
    const response = await fetch(`http://localhost:5163/users`);
    const data = await response.json();
    setUsers(Object.values(data));
  };

  // Send message
  const sendMessage = async () => {
    if (!message.trim()) return;
    await fetch("http://localhost:5163/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.user_id, room, text: message }),
    });
    setMessage("");
    fetchMessages();
  };

  // Logout
  const logout = async () => {
    await fetch("http://localhost:5163/logout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user.user_id }),
    });
    setUser(null);
  };

  // Poll for updates
  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      fetchMessages();
      fetchUsers();
    }, 1000);
    return () => clearInterval(interval);
  }, [room, user]);

  // Render
  return (
    <div className="App">
      {!user ? (
        <div className="register">
          <h1>Welcome to Chat App</h1>
          <input
            type="text"
            placeholder="Enter your name"
            onKeyDown={(e) => e.key === "Enter" && registerUser(e.target.value)}
          />
        </div>
      ) : (
        <div className="chat">
          <div className="sidebar">
            <h2>Rooms</h2>
            <button onClick={() => setRoom("general")}>General</button>
            <button onClick={() => setRoom("random")}>Random</button>
            <h2>Users</h2>
            <ul>
              {users.map((u) => (
                <li key={u.name}>
                  {u.name} {u.online ? "🟢" : "🔴"}
                </li>
              ))}
            </ul>
            <button onClick={logout}>Logout</button>
          </div>
          <div className="messages">
            {messages.map((msg) => (
              <div key={msg.id} className="message">
                <strong>{users.find((u) => u.user_id === msg.user_id)?.name}:</strong> {msg.text}
              </div>
            ))}
          </div>
          <div className="input-area">
            <input
              type="text"
              placeholder="Type a message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
};

// Mounting logic
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
