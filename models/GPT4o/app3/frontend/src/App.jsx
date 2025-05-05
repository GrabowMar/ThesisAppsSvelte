import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  // State Management
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [error, setError] = useState(null);

  // Update form data on user input
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setFeedbackMessage(''); // Clear previous messages
    setError(null);         // Clear previous errors

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setFeedbackMessage(data.message);
        setFormData({ name: '', email: '', message: '' }); // Reset form
      } else {
        setError(data.error || 'An error occurred while submitting feedback.');
      }
    } catch (err) {
      setError('Failed to connect to the server.');
    }
  };

  return (
    <main className="App">
      <h1>Feedback Form</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="name">Name:</label>
          <input
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            required
          />
        </div>

        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            required
          />
        </div>

        <div>
          <label htmlFor="message">Message:</label>
          <textarea
            id="message"
            name="message"
            value={formData.message}
            onChange={handleInputChange}
            required
          />
        </div>

        <button type="submit">Submit Feedback</button>
      </form>

      {feedbackMessage && <p className="success">{feedbackMessage}</p>}
      {error && <p className="error">{error}</p>}
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
