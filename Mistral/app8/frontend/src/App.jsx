import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Route, Switch, Link } from 'react-router-dom';
import './App.css';

// Components
const ThreadList = () => {
    const [threads, setThreads] = useState([]);

    useEffect(() => {
        fetch('/api/threads')
            .then(response => response.json())
            .then(data => setThreads(data));
    }, []);

    return (
        <div>
            <h1>Threads</h1>
            <ul>
                {threads.map(thread => (
                    <li key={thread.id}>
                        <Link to={`/threads/${thread.id}`}>{thread.title}</Link>
                    </li>
                ))}
            </ul>
        </div>
    );
};

const ThreadDetail = ({ match }) => {
    const [thread, setThread] = useState(null);
    const [comment, setComment] = useState('');

    useEffect(() => {
        fetch(`/api/threads/${match.params.id}`)
            .then(response => response.json())
            .then(data => setThread(data));
    }, [match.params.id]);

    const handleSubmit = (event) => {
        event.preventDefault();
        fetch(`/api/threads/${match.params.id}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: comment })
        })
        .then(response => response.json())
        .then(data => {
            setThread(prevThread => ({
                ...prevThread,
                comments: [...prevThread.comments, data]
            }));
            setComment('');
        });
    };

    if (!thread) return <div>Loading...</div>;

    return (
        <div>
            <h1>{thread.title}</h1>
            <p>{thread.content}</p>
            <h2>Comments</h2>
            <ul>
                {thread.comments.map(comment => (
                    <li key={comment.id}>{comment.content}</li>
                ))}
            </ul>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    placeholder="Add a comment"
                />
                <button type="submit">Submit</button>
            </form>
        </div>
    );
};

const App = () => {
    return (
        <Router>
            <div>
                <nav>
                    <Link to="/">Home</Link>
                </nav>
                <Switch>
                    <Route exact path="/" component={ThreadList} />
                    <Route path="/threads/:id" component={ThreadDetail} />
                </Switch>
            </div>
        </Router>
    );
};

// Mounting Logic
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
