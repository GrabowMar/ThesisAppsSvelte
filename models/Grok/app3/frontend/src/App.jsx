// App.jsx

import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const API_URL = 'http://localhost:5485/api';

function App() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [feedbackList, setFeedbackList] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchFeedback();
  }, []);

  const fetchFeedback = async () => {
    try {
      const response = await fetch(`${API_URL}/feedback`);
      if (!response.ok) throw new Error('Failed to fetch feedback');
      const data = await response.json();
      setFeedbackList(data);
    } catch (err) {
      setError('Error fetching feedback: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, feedback }),
      });
      if (!response.ok) throw new Error('Failed to submit feedback');
      const data = await response.json();
      setSubmitted(true);
      setName('');
      setEmail('');
      setFeedback('');
      fetchFeedback();
    } catch (err) {
      setError('Error submitting feedback: ' + err.message);
    }
  };

  if (submitted) {
    return (
      <div className="success-message">
        <h2>Thank you for your feedback!</h2>
        <button onClick={() => setSubmitted(false)}>Submit Another Feedback</button>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>Feedback Form</h1>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="feedback">Feedback:</label>
          <textarea
            id="feedback"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            required
          />
        </div>
        <button type="submit">Submit Feedback</button>
      </form>
      <h2>Recent Feedback</h2>
      <ul className="feedback-list">
        {feedbackList.map((item) => (
          <li key={item.id} className="feedback-item">
            <strong>{item.name}</strong> ({item.email}) - {item.timestamp}
            <p>{item.feedback}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

// Mounting logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

export default App;
