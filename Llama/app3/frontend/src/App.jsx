import React, { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';

function App() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [feedback, setFeedback] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();
    fetch('http://localhost:5005/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, feedback }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setSuccess(true);
          setName('');
          setEmail('');
          setFeedback('');
        }
      })
      .catch((error) => console.error(error));
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <div className="app">
              <h1>Feedback Form</h1>
              <form onSubmit={handleSubmit}>
                <label>
                  Name:
                  <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
                </label>
                <br />
                <label>
                  Email:
                  <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
                </label>
                <br />
                <label>
                  Feedback:
                  <textarea value={feedback} onChange={(event) => setFeedback(event.target.value)} />
                </label>
                <br />
                <input type="submit" value="Submit" />
              </form>
              {success && <p>Thank you for your feedback!</p>}
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
