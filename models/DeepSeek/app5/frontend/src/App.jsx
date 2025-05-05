import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom/client";
import "./App.css";

const App = () => {
  const [page, setPage] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const handleRegister = async () => {
    const response = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    setMessage(data.message);
    if (response.ok) setPage("login");
  };

  const handleLogin = async () => {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
      credentials: "include",
    });
    const data = await response.json();
    setMessage(data.message);
    if (response.ok) setPage("dashboard");
  };

  const handleLogout = async () => {
    const response = await fetch("/api/logout", {
      method: "POST",
      credentials: "include",
    });
    const data = await response.json();
    setMessage(data.message);
    if (response.ok) setPage("login");
  };

  const fetchDashboard = async () => {
    const response = await fetch("/api/dashboard", {
      credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) setPage("login");
    else setMessage(data.message);
  };

  useEffect(() => {
    if (page === "dashboard") fetchDashboard();
  }, [page]);

  return (
    <main>
      {page === "login" && (
        <div className="auth-form">
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
          <p>
            Don't have an account?{" "}
            <span onClick={() => setPage("register")}>Register</span>
          </p>
          {message && <p className="message">{message}</p>}
        </div>
      )}
      {page === "register" && (
        <div className="auth-form">
          <h1>Register</h1>
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
          <button onClick={handleRegister}>Register</button>
          <p>
            Already have an account?{" "}
            <span onClick={() => setPage("login")}>Login</span>
          </p>
          {message && <p className="message">{message}</p>}
        </div>
      )}
      {page === "dashboard" && (
        <div className="dashboard">
          <h1>Dashboard</h1>
          <p>{message}</p>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </main>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
