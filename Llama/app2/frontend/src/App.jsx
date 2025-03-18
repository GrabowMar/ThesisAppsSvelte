import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";
import { io } from "socket.io-client";

const App = () => {
  const [page, setPage] = useState("login"); // For multipage navigation
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [currentUser, setCurrentUser] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState("general");
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Connect to the WebSocket server
    if (currentUser) {
      const newSocket = io("http://localhost:5003");
      setSocket(newSocket);

      // Join the default room
      newSocket.emit("join", { username: currentUser, room: "general" });

      // Listen for new messages
      newSocket.on("message", (data) => {
        setMessages((prevMessages) => [...prevMessages, data]);
      });

      return () => newSocket.disconnect();
    }
  }, [currentUser]);

  // Fetch available rooms on load
  useEffect(() => {
    fetch("http://localhost:5003/rooms")
      .then((res) => res.json())
      .then((data) => setRooms(data.rooms))
      .catch((err) => console.error("Error fetching rooms:", err));
  }, []);

  const handleLogin = () => {
    fetch("http://localhost:5003/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Login failed");
        }
        return res.json();
      })
      .then((data) => {
        setCurrentUser(data.user);
        setPage("chat");
      })
      .catch((err) => alert(err.message));
  };

  const handleRegister = () => {
    fetch("http://localhost:5003/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
      .then((res) => {
        if (!res.ok) {
          throw new Error("Registration failed");
        }
        return res.json();
      })
      .then(() => alert("Registration successful! Please log in."))
      .catch((err) => alert(err.message));
  };

  const handleRoomChange = (room) => {
    if (socket) {
      socket.emit("leave", { username: currentUser, room: currentRoom });
      socket.emit("join", { username: currentUser, room: room });
    }
    setCurrentRoom(room);
    setMessages([]);
  };

  const handleSendMessage = () => {
    if (newMessage.trim() !== "" && socket) {
      socket.emit("message", {
        username: currentUser,
        room: currentRoom,
        message: newMessage,
      });
      setNewMessage("");
    }
  };

  // Pages
  const LoginPage = () => (
    <div className="auth-container">
      <h1>Login</h1>
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
      <button onClick={handleLogin}>Login</button>
      <button onClick={handleRegister}>Register</button>
    </div>
  );

  const ChatPage = () => (
    <div className="chat-container">
      <h1>Welcome, {currentUser}!</h1>
      <div className="room-selector">
        <h4>Rooms:</h4>
        {rooms.map((room) => (
          <button
            key={room}
            className={room === currentRoom ? "active" : ""}
            onClick={() => handleRoomChange(room)}
          >
            {room}
          </button>
        ))}
      </div>
      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className="message">
            <strong>{msg.username}:</strong> {msg.message}
          </div>
        ))}
      </div>
      <div className="message-input">
        <input
          type="text"
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );

  return (
    <div>{page === "login" ? <LoginPage /> : <ChatPage />}</div>
  );
};

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
