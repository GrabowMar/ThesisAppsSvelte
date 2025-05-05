import React, { useEffect, useState } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

const App = () => {
  const [threads, setThreads] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [newThread, setNewThread] = useState({ title: '', content: '', category: '' });

  useEffect(() => {
    fetchThreads();
    fetchCategories();
  }, [selectedCategory, searchQuery]);

  const fetchThreads = async () => {
    let url = '/api/threads?';
    if (selectedCategory) {
      url += `category=${selectedCategory}&`;
    }
    if (searchQuery) {
      url += `search=${searchQuery}`;
    }

    const response = await fetch(url);
    const data = await response.json();
    setThreads(data);
  };

  const fetchCategories = async () => {
    const response = await fetch('/api/categories');
    const data = await response.json();
    setCategories(data);
  };

  const createThread = async () => {
    if (!newThread.title || !newThread.content || !newThread.category) {
      alert('All fields are required!');
      return;
    }

    const response = await fetch('/api/threads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newThread),
    });

    if (response.ok) {
      fetchThreads();
      setNewThread({ title: '', content: '', category: '' });
    } else {
      alert('Failed to create thread!');
    }
  };

  return (
    <div className="App">
      <header>
        <h1>Forum Application</h1>
      </header>
      <div className="filters">
        <input
          type="text"
          placeholder="Search threads..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <select onChange={(e) => setSelectedCategory(e.target.value)} value={selectedCategory}>
          <option value="">All Categories</option>
          {categories.map((category, idx) => (
            <option key={idx} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>
      <div className="threads">
        {threads.map((thread) => (
          <div key={thread.id} className="thread">
            <h3>{thread.title}</h3>
            <p>{thread.content}</p>
            <small>Category: {thread.category}</small>
          </div>
        ))}
      </div>
      <div className="new-thread">
        <h2>Create New Thread</h2>
        <input
          type="text"
          placeholder="Title"
          value={newThread.title}
          onChange={(e) => setNewThread({ ...newThread, title: e.target.value })}
        />
        <textarea
          placeholder="Content"
          value={newThread.content}
          onChange={(e) => setNewThread({ ...newThread, content: e.target.value })}
        />
        <select onChange={(e) => setNewThread({ ...newThread, category: e.target.value })} value={newThread.category}>
          <option value="">Select Category</option>
          {categories.map((category, idx) => (
            <option key={idx} value={category}>
              {category}
            </option>
          ))}
        </select>
        <button onClick={createThread}>Post</button>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
