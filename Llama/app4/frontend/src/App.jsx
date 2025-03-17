// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [feedback, setFeedback] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const [feedbackResponses, setFeedbackResponses] = useState([]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (name && email && feedback) {
            fetch('http://localhost:5007/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, feedback }),
            })
            .then((res) => res.json())
            .then((data) => {
                if (data.message === 'Feedback submitted successfully') {
                    setSubmitted(true);
                    fetchFeedback();
                }
            })
            .catch((err) => console.error(err));
        }
    };

    const fetchFeedback = () => {
        fetch('http://localhost:5007/feedback')
        .then((res) => res.json())
        .then((data) => {
            setFeedbackResponses(data);
        })
        .catch((err) => console.error(err));
    };

    useEffect(() => {
        fetchFeedback();
    }, []);

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={
                    <div>
                        <h1>Feedback Form</h1>
                        <form onSubmit={handleSubmit}>
                            <label>Name:</label>
                            <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
                            <br />
                            <label>Email:</label>
                            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                            <br />
                            <label>Feedback:</label>
                            <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)} />
                            <br />
                            <button type="submit">Submit</button>
                        </form>
                        {submitted && <p>Feedback submitted successfully!</p>}
                    </div>
                } />
                <Route path="/feedback" element={
                    <div>
                        <h1>Feedback Responses</h1>
                        <ul>
                            {feedbackResponses.map((response) => (
                                <li key={response.email}>
                                    <p>Name: {response.name}</p>
                                    <p>Email: {response.email}</p>
                                    <p>Feedback: {response.feedback}</p>
                                </li>
                            ))}
                        </ul>
                    </div>
                } />
            </Routes>
        </BrowserRouter>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
