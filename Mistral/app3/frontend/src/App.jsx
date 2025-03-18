import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';

const FeedbackForm = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [feedback, setFeedback] = useState('');
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        const response = await fetch('http://localhost:5085/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, feedback }),
        });
        const data = await response.json();
        setMessage(data.message);
    };

    return (
        <div className="feedback-form">
            <h2>Submit Feedback</h2>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>Name:</label>
                    <input type="text" value={name} onChange={(e) => setName(e.target.value)} required />
                </div>
                <div>
                    <label>Email:</label>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </div>
                <div>
                    <label>Feedback:</label>
                    <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)} required />
                </div>
                <button type="submit">Submit</button>
            </form>
            {message && <p>{message}</p>}
        </div>
    );
};

const FeedbackList = () => {
    const [feedbacks, setFeedbacks] = useState([]);

    useState(() => {
        fetch('http://localhost:5085/feedback')
            .then(response => response.json())
            .then(data => setFeedbacks(data));
    }, []);

    return (
        <div className="feedback-list">
            <h2>Feedback List</h2>
            <ul>
                {feedbacks.map((feedback, index) => (
                    <li key={index}>
                        <p><strong>Name:</strong> {feedback.name}</p>
                        <p><strong>Email:</strong> {feedback.email}</p>
                        <p><strong>Feedback:</strong> {feedback.feedback}</p>
                    </li>
                ))}
            </ul>
        </div>
    );
};

const App = () => {
    return (
        <Router>
            <div className="app">
                <nav>
                    <Link to="/">Submit Feedback</Link>
                    <Link to="/list">View Feedbacks</Link>
                </nav>
                <Routes>
                    <Route path="/" element={<FeedbackForm />} />
                    <Route path="/list" element={<FeedbackList />} />
                </Routes>
            </div>
        </Router>
    );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
