// app/frontend/src/App.jsx

import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Main App component demonstrating multipage routing with conditional rendering.
function App() {
  // "page" state for multipage routing: 'feedback', 'login', or 'dashboard'
  const [page, setPage] = useState('feedback');
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [notification, setNotification] = useState({ type: '', message: '' });
  const [errors, setErrors] = useState({});
  
  // Handle input changes for the feedback form.
  const handleChange = (e) => {
    setFormData(prevData => ({ ...prevData, [e.target.name]: e.target.value }));
  };

  // Validate formData before submission.
  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.message.trim()) newErrors.message = 'Feedback message is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit feedback to backend /api/feedback endpoint
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setNotification({ type: 'error', message: 'Please fix the errors and try again.' });
      return;
    }

    try {
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        // Handle error state response from backend.
        const errorData = await response.json();
        setNotification({ type: 'error', message: errorData.message || 'Submission failed' });
      } else {
        const data = await response.json();
        setNotification({ type: 'success', message: data.message });
        // Reset form data upon successful submission.
        setFormData({ name: '', email: '', message: '' });
        setErrors({});
      }
    } catch (error) {
      setNotification({ type: 'error', message: 'Network error. Please try again later.' });
    }
  };

  // Render different views based on "page" state.
  const renderPage = () => {
    switch (page) {
      case 'feedback':
        return (
          <div className="form-container">
            <h2>Feedback Form</h2>
            {notification.message && (
              <div className={`notification ${notification.type}`}>
                {notification.message}
              </div>
            )}
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Name:</label>
                <input 
                  type="text" 
                  name="name" 
                  id="name" 
                  value={formData.name} 
                  onChange={handleChange} 
                />
                {errors.name && <span className="error">{errors.name}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="email">Email:</label>
                <input 
                  type="email" 
                  name="email" 
                  id="email" 
                  value={formData.email} 
                  onChange={handleChange} 
                />
                {errors.email && <span className="error">{errors.email}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="message">Feedback:</label>
                <textarea 
                  name="message" 
                  id="message" 
                  value={formData.message} 
                  onChange={handleChange} 
                />
                {errors.message && <span className="error">{errors.message}</span>}
              </div>
              <button type="submit">Submit Feedback</button>
            </form>
          </div>
        );
      case 'login':
        return (
          <div className="page-container">
            <h2>Login Page</h2>
            <p>This page is under construction. (Dummy page for multipage routing)</p>
            {/* Add login form if needed */}
          </div>
        );
      case 'dashboard':
        return (
          <div className="page-container">
            <h2>Dashboard</h2>
            <p>This page is under construction. (Dummy page for multipage routing)</p>
            {/* Dashboard logic would go here; e.g., fetching feedbacks */}
          </div>
        );
      default:
        return <div>Page not found.</div>;
    }
  };

  return (
    <div className="app">
      <header>
        <h1>Feedback System</h1>
        <nav>
          <button onClick={() => setPage('feedback')}>Feedback</button>
          <button onClick={() => setPage('login')}>Login</button>
          <button onClick={() => setPage('dashboard')}>Dashboard</button>
        </nav>
      </header>
      <main>
        {renderPage()}
      </main>
      <footer>
        <p>&copy; {new Date().getFullYear()} Feedback System</p>
      </footer>
    </div>
  );
}

// Mounting logic: attach the main App component to the DOM element with id "root"
const rootElement = document.getElementById("root");
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);

export default App;
