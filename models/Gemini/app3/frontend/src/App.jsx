// 1. Imports
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css'; // Import CSS
import ThankYouPage from './ThankYouPage'; // Import the ThankYouPage component


// 2. State Management
function App() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [feedback, setFeedback] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showThankYou, setShowThankYou] = useState(false);



    // 4. Event Handlers
    const handleSubmit = async (e) => {
        e.preventDefault();
        setErrorMessage(''); // Clear any previous errors
        setSuccessMessage(''); // Clear any previous success message
        setIsLoading(true);

        // Validation
        if (!name.trim() || !email.trim() || !feedback.trim()) {
            setErrorMessage('Please fill in all fields.');
            setIsLoading(false);
            return;
        }

        if (!email.includes('@') || !email.includes('.')) {
            setErrorMessage('Please enter a valid email address.');
            setIsLoading(false);
            return;
        }

        // 5. API Calls
        try {
            const response = await fetch('/api/submit_feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, feedback }),
            });

            const data = await response.json();

            if (response.ok && data.success) {
                setSuccessMessage(data.message);
                setName('');
                setEmail('');
                setFeedback('');
                setShowThankYou(true);  // Show the thank you page
            } else {
                setErrorMessage(data.message || 'Failed to submit feedback.');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            setErrorMessage('Failed to submit feedback. Please try again later.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoBack = () => {
        setShowThankYou(false);
    };


    // Conditional rendering: Show feedback form or thank you page
    if (showThankYou) {
        return <ThankYouPage onGoBack={handleGoBack} />;
    }

    // 6. UI Components
    return (
        <div className="app-container">
            <h1>Feedback Form</h1>
            {errorMessage && <div className="error-message">{errorMessage}</div>}
            {successMessage && <div className="success-message">{successMessage}</div>}
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
                    ></textarea>
                </div>
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Submitting...' : 'Submit Feedback'}
                </button>
            </form>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<React.StrictMode><App /></React.StrictMode>);

export default App;
