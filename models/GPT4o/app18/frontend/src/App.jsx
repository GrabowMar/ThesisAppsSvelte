import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

// Backend API base URL
const API_BASE = 'http://localhost:5275/api';

const App = () => {
  const [view, setView] = useState('list'); // 'list', 'editor', 'view'
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [editorContent, setEditorContent] = useState('');
  const [editorName, setEditorName] = useState('');

  // Load all pages
  useEffect(() => {
    loadPages();
  }, []);

  const loadPages = async () => {
    const response = await fetch(`${API_BASE}/search`);
    const data = await response.json();
    setPages(Object.keys(data));
  };

  const handleCreatePage = (e) => {
    e.preventDefault();
    setView('editor');
    setEditorName('');
    setEditorContent('');
  };

  const handleViewPage = (name) => {
    fetch(`${API_BASE}/page/${name}`)
      .then((res) => res.json())
      .then((data) => {
        setCurrentPage(data);
        setView('view');
      });
  };

  const handleSavePage = (e) => {
    e.preventDefault();
    fetch(`${API_BASE}/page`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: editorName, content: editorContent }),
    }).then(() => {
      loadPages();
      setView('list');
    });
  };

  return (
    <div className="App">
      <header>
        <h1>Wiki System</h1>
        <nav>
          <button onClick={() => setView('list')}>Home</button>
          <button onClick={handleCreatePage}>Create Page</button>
        </nav>
        <input
          type="text"
          placeholder="Search pages..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button onClick={loadPages}>Search</button>
      </header>

      <main>
        {view === 'list' && (
          <div>
            <h2>All Pages</h2>
            <ul>
              {pages.map((page) => (
                <li key={page}>
                  {page}{' '}
                  <button onClick={() => handleViewPage(page)}>View</button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {view === 'view' && currentPage && (
          <div>
            <h2>Viewing: {currentPage.name}</h2>
            <div className="page-content">{currentPage.content}</div>
            <button onClick={() => setView('list')}>Back</button>
          </div>
        )}

        {view === 'editor' && (
          <form onSubmit={handleSavePage}>
            <h2>{editorName ? 'Edit Page' : 'Create Page'}</h2>
            <input
              type="text"
              placeholder="Page Name"
              value={editorName}
              onChange={(e) => setEditorName(e.target.value)}
              required
            />
            <textarea
              placeholder="Page Content"
              value={editorContent}
              onChange={(e) => setEditorContent(e.target.value)}
              required
            />
            <button type="submit">Save</button>
          </form>
        )}
      </main>
    </div>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
