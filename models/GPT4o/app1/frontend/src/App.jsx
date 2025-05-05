// App.jsx
import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

function App() {
  const [page, setPage] = useState("login"); // control multipage routing
  const [message, setMessage] = useState("");
  const [user, setUser] = useState(null);

  // API calls
  const handleRegister = async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const username = form.get("username");
    const password = form.get("password");

    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();
    setMessage(data.message || data.error);
    if (res.ok) setPage("login");
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const form = new FormData(e.target);
    const username = form.get("username");
    const password = form.get("password");

    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();
    setMessage(data.message || data.error);
    if (res.ok) setUser(username);
  };

  const handleLogout = async () => {
    await fetch("/api/logout", { method: "POST" });
    setUser(null);
    setMessage("Logged out");
  };

  // Render Pages
  if (user) {
    return (
      <div>
        <h1>Dashboard</h1>
        <p>Welcome, {user}!</p>
        <button onClick={handleLogout}>Logout</button>
      </div>
    );
  }

  return (
    <div>
      <h1>{page === "login" ? "Login" : "Register"}</h1>
      <form onSubmit={page === "login" ? handleLogin : handleRegister}>
        <input type="text" name="username" placeholder="Username" required />
        <input type="password" name="password" placeholder="Password" required />
        <button type="submit">{page === "login" ? "Login" : "Register"}</button>
      </form>
      <button onClick={() => setPage(page === "login" ? "register" : "login")}>
        {page === "login" ? "Switch to Register" : "Switch to Login"}
      </button>
      <p>{message}</p>
    </div>
  );
}

// Mount App
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
