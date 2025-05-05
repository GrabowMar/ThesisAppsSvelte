import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Link, useHistory } from 'react-router-dom';
import axios from 'axios';
import ReactDOM from 'react-dom/client';
import './App.css';
const App = () => {
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [connections, setConnections] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [messages, setMessages] = useState([]);
  const history = useHistory();
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get('/profile', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }).then(response => {
        setProfile(response.data);
      }).catch(error => {
        console.error("Error fetching profile:", error);
      });
    }
  }, []);
  const handleRegister = (event) => {
    event.preventDefault();
    const { username, email, password } = event.target.elements;
    axios.post('/register', {
      username: username.value,
      email: email.value,
      password: password.value
    }).then(response => {
      history.push('/login');
    }).catch(error => {
      console.error("Error registering:", error);
    });
  };

  const handleLogin = (event) => {
    event.preventDefault();
    const { email, password } = event.target.elements;
    axios.post('/login', {
      email: email.value,
      password: password.value
    }).then(response => {
      localStorage.setItem('token', response.data.access_token);
      setUser(response.data);
      history.push('/dashboard');
    }).catch(error => {
      console.error("Error logging in:", error);
    });
  };

  const fetchProfile = () => {
    const token = localStorage.getItem('token');
    axios.get('/profile', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }).then(response => {
      setProfile(response.data);
    }).catch(error => {
      console.error("Error fetching profile:", error);
    });
  };

  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
      <Switch>
        <Route path="/register">
          <form onSubmit={handleRegister}>
            <input type="text" name="username" placeholder="Username" required />
            <input type="email" name="email" placeholder="Email" required />
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit">Register</button>
          </form>
        </Route>
        <Route path="/login">
          <form onSubmit={handleLogin}>
            <input type="email" name="email" placeholder="Email" required />
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit">Login</button>
          </form>
        </Route>
        <Route path="/dashboard">
          <div>
            <h1>Dashboard</h1>
            {profile && <div>{profile.bio}</div>}
          </div>
        </Route>
        <Route path="/">
          <h1>Welcome to the Professional Networking System</h1>
        </Route>
      </Switch>
    </Router>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;

