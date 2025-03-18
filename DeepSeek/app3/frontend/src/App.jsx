import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [rating, setRating] = useState('');
  const [comments, setComments] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const validateForm = () => {
    if (!name || !email || !rating || !comments) {
      setErrorMessage('All fields are required');
      return false;
    }
    if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i.test(email)) {
      setErrorMessage('Invalid email address');
      return false;
    }
    if (rating < 1 || rating > 5) {
      setErrorMessage('Rating must be between 1 and 5');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (!validateForm()) return;

    try {
      const response = await fetch('http://localhost:5165/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, rating, comments }),
      });
      if (!response.ok) throw new Error('Failed to submit feedback');
      setSuccessMessage('Thank you for your feedback!');
      setName('');
      setEmail('');
      setRating('');
      setComments('');
    } catch (error) {
      setErrorMessage('Failed to submit feedback. Please try again.');
    }
  };

  return (
    <div className="App">
      <h1>Feedback Form</h1>
      {successMessage && <p className="success">{successMessage}</p>}
      {errorMessage && <p className="error">{errorMessage}</p>}
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Email:
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Rating (1-5):
          <input
            type="number"
            min="1"
            max="5"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
          />
        </label>
        <label>
          Comments:
          <textarea value={comments} onChange={(e) => setComments(e.target.value)} />
        </label>
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}

// Mounting logic
ReactDOM.createRoot(document.getElementById('root')).render(<App />);
