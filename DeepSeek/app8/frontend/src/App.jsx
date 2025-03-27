import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
    const [threads, setThreads] = useState([]);
    const [newThread, setNewThread] = useState({ title: '', category: '', content: '' });
    const [newComment, setNewComment] = useState({ threadId: '', content: '' });
    const [search, setSearch] = useState('');
    const [sort, setSort] = useState('latest');

    useEffect(() => {
        fetchThreads();
    }, [search, sort]);

    const fetchThreads = async () => {
        const response = await fetch(`/api/threads?search=${search}&sort=${sort}`);
        const data = await response.json();
        setThreads(data);
    };

    const handleCreateThread = async () => {
        const response = await fetch('/api/threads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newThread)
        });
        const data = await response.json();
        setThreads([...threads, data]);
        setNewThread({ title: '', category: '', content: '' });
    };

    const handleAddComment = async (threadId) => {
        const response = await fetch(`/api/threads/${threadId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newComment)
        });
        const data = await response.json();
        const updatedThreads = threads.map(t =>
            t.id === threadId ? { ...t, comments: [...t.comments, data] } : t
        );
        setThreads(updatedThreads);
        setNewComment({ ...newComment, content: '' });
    };

    return (
        <main>
            <h1>Forum</h1>
            <div className="controls">
                <input
                    type="text"
                    placeholder="Search threads..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <select value={sort} onChange={(e) => setSort(e.target.value)}>
                    <option value="latest">Latest</option>
                    <option value="oldest">Oldest</option>
                </select>
            </div>
            <div className="thread-form">
                <input
                    type="text"
                    placeholder="Title"
                    value={newThread.title}
                    onChange={(e) => setNewThread({ ...newThread, title: e.target.value })}
                />
                <input
                    type="text"
                    placeholder="Category"
                    value={newThread.category}
                    onChange={(e) => setNewThread({ ...newThread, category: e.target.value })}
                />
                <textarea
                    placeholder="Content"
                    value={newThread.content}
                    onChange={(e) => setNewThread({ ...newThread, content: e.target.value })}
                />
                <button onClick={handleCreateThread}>Create Thread</button>
            </div>
            <div className="threads">
                {threads.map(thread => (
                    <div key={thread.id} className="thread">
                        <h2>{thread.title}</h2>
                        <p>{thread.content}</p>
                        <div className="comments">
                            {thread.comments.map(comment => (
                                <div key={comment.id} className="comment">
                                    <p>{comment.content}</p>
                                </div>
                            ))}
                            <textarea
                                placeholder="Add a comment"
                                value={newComment.threadId === thread.id ? newComment.content : ''}
                                onChange={(e) => setNewComment({ threadId: thread.id, content: e.target.value })}
                            />
                            <button onClick={() => handleAddComment(thread.id)}>Add Comment</button>
                        </div>
                    </div>
                ))}
            </div>
        </main>
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
