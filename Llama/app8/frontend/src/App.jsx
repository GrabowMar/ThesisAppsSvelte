// App.jsx
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import axios from 'axios';
import './App.css';

function App() {
    const [threads, setThreads] = useState([]);
    const [newThreadTitle, setNewThreadTitle] = useState('');
    const [newThreadCategory, setNewThreadCategory] = useState('');
    const [selectedThread, setSelectedThread] = useState(null);
    const [newCommentContent, setNewCommentContent] = useState('');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        axios.get('http://localhost:5015/threads')
            .then(response => {
                setThreads(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    }, []);

    const handleCreateThread = (event) => {
        event.preventDefault();
        axios.post('http://localhost:5015/threads', {
            title: newThreadTitle,
            category: newThreadCategory
        })
            .then(response => {
                setThreads([...threads, response.data]);
                setNewThreadTitle('');
                setNewThreadCategory('');
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleSelectThread = (thread) => {
        setSelectedThread(thread);
        axios.get(`http://localhost:5015/threads/${thread.id}/comments`)
            .then(response => {
                thread.comments = response.data;
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleCreateComment = (event) => {
        event.preventDefault();
        axios.post(`http://localhost:5015/threads/${selectedThread.id}/comments`, {
            content: newCommentContent
        })
            .then(response => {
                selectedThread.comments.push(response.data);
                setNewCommentContent('');
            })
            .catch(error => {
                console.error(error);
            });
    };

    const handleSearch = (event) => {
        event.preventDefault();
        axios.get(`http://localhost:5015/threads/search?query=${searchQuery}`)
            .then(response => {
                setThreads(response.data);
            })
            .catch(error => {
                console.error(error);
            });
    };

    return (
        <div className="app">
            <h1>Forum Application</h1>
            <form onSubmit={handleCreateThread}>
                <input
                    type="text"
                    value={newThreadTitle}
                    onChange={(event) => setNewThreadTitle(event.target.value)}
                    placeholder="Thread title"
                />
                <input
                    type="text"
                    value={newThreadCategory}
                    onChange={(event) => setNewThreadCategory(event.target.value)}
                    placeholder="Thread category"
                />
                <button type="submit">Create Thread</button>
            </form>
            <ul>
                {threads.map((thread) => (
                    <li key={thread.id}>
                        <a onClick={() => handleSelectThread(thread)}>{thread.title}</a>
                    </li>
                ))}
            </ul>
            {selectedThread && (
                <div>
                    <h2>{selectedThread.title}</h2>
                    <ul>
                        {selectedThread.comments && selectedThread.comments.map((comment) => (
                            <li key={comment.id}>{comment.content}</li>
                        ))}
                    </ul>
                    <form onSubmit={handleCreateComment}>
                        <input
                            type="text"
                            value={newCommentContent}
                            onChange={(event) => setNewCommentContent(event.target.value)}
                            placeholder="Comment content"
                        />
                        <button type="submit">Create Comment</button>
                    </form>
                </div>
            )}
            <form onSubmit={handleSearch}>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(event) => setSearchQuery(event.target.value)}
                    placeholder="Search query"
                />
                <button type="submit">Search</button>
            </form>
        </div>
    );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
