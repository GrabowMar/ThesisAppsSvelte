import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';

function App() {
  const [pages, setPages] = useState([]);
  const [currentPage, setCurrentPage] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [view, setView] = useState('list'); // list, create, edit, history
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  useEffect(() => {
    fetch('/api/pages')
      .then((res) => res.json())
      .then(setPages);
  }, []);

  const handleSearch = () => {
    fetch(`/api/search?q=${searchQuery}`)
      .then((res) => res.json())
      .then(setSearchResults);
  };

  const handleCreatePage = () => {
    fetch('/api/pages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content }),
    })
      .then((res) => res.json())
      .then((data) => {
        setPages([...pages, data]);
        setView('list');
      });
  };

  const handleEditPage = (pageId) => {
    fetch(`/api/pages/${pageId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    })
      .then((res) => res.json())
      .then((data) => {
        setCurrentPage(data);
        setView('list');
      });
  };

  const renderView = () => {
    switch (view) {
      case 'create':
        return (
          <div>
            <h2>Create Page</h2>
            <input
              type="text"
              placeholder="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <textarea
              placeholder="Content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <button onClick={handleCreatePage}>Save</button>
            <button onClick={() => setView('list')}>Cancel</button>
          </div>
        );
      case 'edit':
        return (
          <div>
            <h2>Edit Page</h2>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <button onClick={() => handleEditPage(currentPage.id)}>Save</button>
            <button onClick={() => setView('list')}>Cancel</button>
          </div>
        );
      case 'history':
        return (
          <div>
            <h2>Version History</h2>
            <ul>
              {currentPage.history.map((version, index) => (
                <li key={index}>
                  <p>{version.content}</p>
                  <small>{version.timestamp}</small>
                </li>
              ))}
            </ul>
            <button onClick={() => setView('list')}>Back</button>
          </div>
        );
      default:
        return (
          <div>
            <h1>Wiki Pages</h1>
            <div>
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button onClick={handleSearch}>Search</button>
            </div>
            <button onClick={() => setView('create')}>Create New Page</button>
            <ul>
              {(searchResults.length ? searchResults : pages).map((page) => (
                <li key={page.id}>
                  <h3>{page.title}</h3>
                  <p>{page.content}</p>
                  <button onClick={() => { setCurrentPage(page); setView('edit'); }}>Edit</button>
                  <button onClick={() => { setCurrentPage(page); setView('history'); }}>History</button>
                </li>
              ))}
            </ul>
          </div>
        );
    }
  };

  return <main>{renderView()}</main>;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
