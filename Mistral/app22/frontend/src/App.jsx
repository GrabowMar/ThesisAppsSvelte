// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link, useHistory } from 'react-router-dom';
import axios from 'axios';
import './App.css';

const App = () => {
  const [user, setUser] = useState(null);
  const history = useHistory();

  useEffect(() => {
    // Fetch user data or any initial data
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    const data = { username: e.target.username.value, password: e.target.password.value };
    const response = await axios.post('/api/login', data);
    if (response.data.message === "Login successful") {
      setUser(data.username);
      history.push('/dashboard');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const data = { username: e.target.username.value, password: e.target.password.value };
    const response = await axios.post('/api/register', data);
    if (response.data.message === "Registration successful") {
      history.push('/login');
    }
  };

  return (
    <Router>
      <nav>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/vocabulary">Vocabulary</Link>
        <Link to="/grammar">Grammar</Link>
        <Link to="/progress">Progress</Link>
        <Link to="/quiz">Quiz</Link>
        <Link to="/pronunciation">Pronunciation</Link>
        <Link to="/multilingual">Multilingual</Link>
      </nav>
      <Switch>
        <Route path="/login">
          <form onSubmit={handleLogin}>
            <input type="text" name="username" placeholder="Username" />
            <input type="password" name="password" placeholder="Password" />
            <button type="submit">Login</button>
          </form>
        </Route>
        <Route path="/register">
          <form onSubmit={handleRegister}>
            <input type="text" name="username" placeholder="Username" />
            <input type="password" name="password" placeholder="Password" />
            <button type="submit">Register</button>
          </form>
        </Route>
        <Route path="/dashboard">
          <h1>Dashboard</h1>
        </Route>
        <Route path="/vocabulary">
          <h1>Vocabulary Lessons</h1>
        </Route>
        <Route path="/grammar">
          <h1>Grammar Exercises</h1>
        </Route>
        <Route path="/progress">
          <h1>Progress Tracking</h1>
        </Route>
        <Route path="/quiz">
          <h1>Quiz/Assessment</h1>
        </Route>
        <Route path="/pronunciation">
          <h1>Pronunciation Guides</h1>
        </Route>
        <Route path="/multilingual">
          <h1>Multilingual Support</h1>
        </Route>
      </Switch>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
