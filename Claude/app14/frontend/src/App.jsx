import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import './App.css';

function Login() {
  return <div>Login Page</div>;
}

function Register() {
  return <div>Register Page</div>;
}

function Dashboard() {
  const [files, setFiles] = useState([]);

  const handleFileUpload = (event) => {
    const formData = new FormData();
    formData.append('file', event.target.files[0]);
    fetch('http://localhost:5107/upload', {
      method: 'POST',
      body: formData,
    }).then(response => response.json())
      .then(data => {
        if (data.message) {
          setFiles([...files, event.target.files[0].name]);
        }
      });
  };

  return (
    <div>
      <h1>Dashboard</h1>
      <input type="file" onChange={handleFileUpload} />
      <ul>
        {files.map((file, index) => (
          <li key={index}>{file}</li>
        ))}
      </ul>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Switch>
        <Route path="/login" component={Login} />
        <Route path="/register" component={Register} />
        <Route path="/dashboard" component={Dashboard} />
      </Switch>
    </Router>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
