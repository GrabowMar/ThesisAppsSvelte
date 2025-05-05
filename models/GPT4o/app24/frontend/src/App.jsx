import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [route, setRoute] = useState('home');
  const [jobs, setJobs] = useState([]);
  const [connections, setConnections] = useState([]);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (route === 'dashboard') {
      fetch('/api/jobs').then(res => res.json()).then(setJobs);
      fetch('/api/connections').then(res => res.json()).then(setConnections);
      fetch('/api/messages').then(res => res.json()).then(setMessages);
    }
  }, [route]);

  return (
    <div className="App">
      <header>
        <h1>Professional Networking Platform</h1>
        <nav>
          <button onClick={() => setRoute('home')}>Home</button>
          <button onClick={() => setRoute('register')}>Register</button>
          <button onClick={() => setRoute('login')}>Login</button>
          <button onClick={() => setRoute('dashboard')}>Dashboard</button>
        </nav>
      </header>

      {route === 'home' && (
        <main>
          <h2>Welcome to the Platform</h2>
          <p>An all-in-one platform to jumpstart your career network.</p>
        </main>
      )}

      {route === 'register' && <Register />}
      {route === 'login' && <Login onLogin={() => setRoute('dashboard')} />}
      {route === 'dashboard' && <Dashboard jobs={jobs} connections={connections} messages={messages} />}
    </div>
  );
}

function Register() {
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('/api/register', { method: 'POST', body: JSON.stringify(formData), headers: { 'Content-Type': 'application/json' } })
      .then(res => res.json())
      .then(data => alert(data.message || data.error))
      .catch(() => alert('Error registering user'));
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Register</h2>
      <input type="text" placeholder="Name" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} required />
      <input type="email" placeholder="Email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required />
      <input type="password" placeholder="Password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required />
      <button type="submit">Register</button>
    </form>
  );
}

function Login({ onLogin }) {
  const [formData, setFormData] = useState({ email: '', password: '' });

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('/api/login', { method: 'POST', body: JSON.stringify(formData), headers: { 'Content-Type': 'application/json' } })
      .then(res => res.json())
      .then(data => {
        alert(data.message || data.error);
        if (data.message) onLogin();
      })
      .catch(() => alert('Error logging in'));
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      <input type="email" placeholder="Email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} required />
      <input type="password" placeholder="Password" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} required />
      <button type="submit">Login</button>
    </form>
  );
}

function Dashboard({ jobs, connections, messages }) {
  return (
    <main>
      <h2>Dashboard</h2>
      <section>
        <h3>Jobs</h3>
        <ul>{jobs.map((job, index) => <li key={index}>{job.title} - {job.company}</li>)}</ul>
      </section>
      <section>
        <h3>Connections</h3>
        <ul>{connections.map((connection, index) => <li key={index}>{connection.name}</li>)}</ul>
      </section>
      <section>
        <h3>Messages</h3>
        <ul>{messages.map((message, index) => <li key={index}>{message.content}</li>)}</ul>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
