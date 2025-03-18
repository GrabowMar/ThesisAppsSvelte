import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
    const [name, setName] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!name || !message) {
            setError('Name and message are required.');
            return;
        }

        if (message.length < 10) {
            setError('Message must be at least 10 characters long.');
            return;
        }

        try {
            const response = await fetch('http://localhost:5000/submit-feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, message }),
            });

            if (!response.ok) {
                throw new Error('Failed to submit feedback.');
            }

            const result = await response.json();
            setSuccess(result.message);
            setName('');
            setMessage('');
        } catch (err) {
            setError('An error occurred while submitting feedback.');
        }
    };

    return (
        <div className="app">
            <h1>Feedback Form</h1>
            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label>Name:</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label>Message:</label>
                    <textarea
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        required
                    />
                </div>
                {error && <p className="error">{error}</p>}
                {success && <p className="success">{success}</p>}
                <button type="submit">Submit</button>
            </form>
        </div>
    );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
